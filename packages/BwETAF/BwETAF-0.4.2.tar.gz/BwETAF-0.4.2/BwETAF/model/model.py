from .layers import *
import flax.serialization
from . ._errors import *
import matplotlib.pyplot as plt
from scipy.ndimage import gaussian_filter1d
from tqdm import tqdm
from . .independent import *
from . ._errors import *
from . .common_imports import *
from . ._utils import TrainRailGuard
import math

import gc
### Constants
rng = jax.random.PRNGKey(0)

class Model(nn.Module):
    num_heads: int | tuple
    attention_dim: int
    vocab_size: int
    num_blocks: int
    ff_dim: int
    dropout_rate: float
    max_len: int
    emb_spl: int
    use_fash_attention: bool = False
    use_rope: bool = False
    dtype: jnp.dtype = jnp.float32


    def setup(self):
        self.emb = nn.Embed(
             num_embeddings=self.vocab_size,
             features=self.attention_dim,
             embedding_init=nn.initializers.normal(stddev=0.02),
             dtype=self.dtype
             )
        
        if not self.use_rope:
            self.pos_encoding = PosEnc(self.attention_dim,self.dtype)
        
        if isinstance(self.num_heads, tuple):
            if len(self.num_heads) == self.num_blocks:
                pass
            else:
                print("Using flash attention") if self.use_fash_attention else None
                raise ModelHpMismatch(f"Model needs a list of heads which is the length of the number of blocks. Here number of heads {len(self.num_heads)} and Number of blocks {self.num_blocks} are not equal.")
            self.blocks = [Block(num_heads=i,attention_dim=self.attention_dim,ff_dim=self.ff_dim,dropout_rate=self.dropout_rate,flash_attn=self.use_fash_attention,dtype=self.dtype)for i in self.num_heads]
        elif isinstance(self.num_heads, int):
            self.blocks = [Block(num_heads=self.num_heads,attention_dim=self.attention_dim,ff_dim=self.ff_dim,dropout_rate=self.dropout_rate,flash_attn=self.use_fash_attention,dtype=self.dtype)for _ in range(self.num_blocks)]
        else:
             raise DebugError(f"Bruh! What? So num head is not a list of a string? It's a {self.num_heads}")
    
    def __call__(self,x,mask,training=True):
        mask = self.process_mask(mask)
        x = x.astype(jnp.uint16)
        x = self.emb(x) * math.sqrt(self.attention_dim)

        if self.use_rope:
            x = RoPE(x,self.max_len)
        else:
            x = self.pos_encoding(x)

        for i in self.blocks:
            x = i(x,mask,training)
        return lax_matmul(x, self.emb.embedding, (2,), (1,),(),(P("data", None, None),P("model", None)))

    def process_mask(self,mask):
        batch_size, seq_len = mask.shape

        # Create causal mask (lower triangular matrix)
        causal_mask = jnp.tril(jnp.ones((seq_len, seq_len)))

        # Reshape padding mask and apply to causal mask
        mask = mask[:, None, :]  # (batch_size, 1, seq_len)
        mask_sq = causal_mask[None, :, :] * mask  # (batch_size, seq_len, seq_len)
        mask_sq = jnp.transpose(mask_sq, (0, 2, 1)) * mask
        mask_sq = jnp.transpose(mask_sq, (0, 2, 1))[:, None, :]
        #mask_sq = jnp.broadcast_to(mask_sq, (batch_size, self.num_heads, seq_len, seq_len))
        return jnp.array(mask_sq)
    
    def last_layer(self,x):
        return lax_matmul(x, self.emb.embedding, (2,), (1,),(),(P("data", None, None),P("model", None)))
    
    def blocks(self,x,mask,training=True):
        mask = self.process_mask(mask)
        x = x.astype(jnp.uint16)
        x = self.emb(x) * math.sqrt(self.attention_dim)

        if self.use_rope:
            x = RoPE(x,self.max_len)
        else:
            x = self.pos_encoding(x)

        for i in self.blocks:
            x = i(x,mask,training)
        return x
        

class ModelManager():
    @debug_state.trace_func
    def __init__(
        self,
        num_heads: tuple,
        attention_dim: int,
        vocab_size: int,
        num_blocks: int,
        ff_dim: int,
        dropout_rate: float,
        max_len: int,
        emb_spl: int = 256,
        dtype=None,
        possible_opt_path: str = "",
        *args,
        **kwargs
    ) -> None:
        self.key = jax.random.PRNGKey(0)
        self.num_blocks = num_blocks
        self.model_struct = Model(num_heads,attention_dim,vocab_size,num_blocks,ff_dim,dropout_rate,max_len,emb_spl,kwargs.get("use_fash_attention"),kwargs.get("use_rope"),dtype)
        self.params = self.model_struct.init(self.key,jax.random.normal(self.key,(2, 11)),jnp.ones((2,11))) 
        if dtype is not None:
            self.params = tree_fn.convert_tree(dtype,self.params)
        self.optimizer = None
        self.possible_opt_path = possible_opt_path

        self.data = {
            "num_heads":num_heads,
            "attention_dim":attention_dim,
            "vocab_size":vocab_size,
            "num_blocks":num_blocks,
            "ff_dim":ff_dim,
            "dropout_rate":dropout_rate,
            'possible_opt_path':possible_opt_path,
            "max_len":max_len,
            'emb_splt':emb_spl,
            'use_fash_attention': kwargs.get("use_fash_attention", False),
            'use_rope': kwargs.get("use_rope", False)
        }
        gc.collect()

    def __call__(self,input,mask):
        return self.model_struct.apply(self.params,input,mask,rngs={"dropout": self.key},training=False)
    
    @partial(jax.jit,static_argnums=(0))
    def jax_call(self,input,mask):
        return self.model_struct.apply(self.params,input,mask,rngs={"dropout": self.key},training=False)
    

    @property
    def trainable_variables(self):
        return self.params
    
    @property
    def key_bruh(self):
        self.key, subkey = jax.random.split(self.key)
        return subkey
    
    @debug_state.trace_func
    def training_setup(self,optimizer,lr,lrf,batches,epochs,state_path="",opt_state_dtype=None):
        self.optimizer = Optimizer(optimizer,lr,lrf,batches,epochs,self.params,opt_state_dtype)
        if state_path == "":
            self.optimizer.load(self.possible_opt_path,opt_state_dtype)
        else:
            self.optimizer.load(state_path,opt_state_dtype)
        self.grad_fn = jax.value_and_grad(loss_fn)
        return self.optimizer.lr_schedule
    
    @debug_state.trace_func
    def train_batch(self,x,mask,y):
        key = self.key_bruh
        loss, self.params, self.optimizer.state = BatchTrain(self.params,self.grad_fn,self.model_struct,x,mask,y,key,self.optimizer.optimizer,self.optimizer.state,self.chunks)
        return loss , [0,0,0]
    
    @debug_state.trace_func
    def save_model(self,name,opt_state=True):
        os.makedirs(name, exist_ok=True)
        with open(os.path.join(name, "good_stuff.pkl"), "wb") as f:
            f.write(flax.serialization.to_bytes(self.trainable_variables))

        with open(os.path.join(name, "understanding_good_stuff.json"),"w") as f:
            json.dump(self.data, f, indent=2)
        
        if (opt_state) and (self.optimizer is not None):
            with open(os.path.join(name, "make_stuff_better.pkl"), "wb") as f:
                f.write(flax.serialization.to_bytes(self.optimizer.state))

    @debug_state.trace_func
    def batch_it(self, x, mask, y, batch_size, x_eq_y=True):
        dataset = Flax_ds(x_eq_y)
        dataset.load_data(x,mask,y)
        dataset.batch_it_(batch_size=batch_size)
        return dataset

    @debug_state.trace_func
    def train(self,x,mask,y,epochs,batch_size,optimizer,lr,lrf,val_x=None,val_mask=None,val_y=None,val_step=100,updates_in=1,avg_mem=1500,state_path=None,chunks=1):
        pass
    #Sry no peaking :p
    
    @debug_state.trace_func
    def summary(self):
        def count_params(params):
            total = 0
            for value in params.values():
                if isinstance(value, dict):
                    total += count_params(value)
                elif hasattr(value, 'size'):
                    total += value.size
            return total
        
        for i in list(self.trainable_variables['params'].keys()):
            print(f"{i} :{count_params(self.trainable_variables['params'].get(i, {})):,}")
        print("-------------------")
        print(f"Total :{count_params(self.trainable_variables['params']):,}")
        gc.collect()
    
    @debug_state.trace_func
    def change_precision(self,dtype):
        self.params = jax.tree_util.tree_map(lambda x: x.astype(dtype),self.params)
        gc.collect()

    @property
    def precision(self):
        type_tree = jax.tree_util.tree_map(lambda x: x.dtype,self.model)
        types = jax.tree_util.tree_leaves(type_tree)
        if len(set(types)) == 1:
            print(f"Model dtype:{types[0]}")
        else:
            print("Model contains mixed dtypes")
        gc.collect()



### Test stuff for now ok?
### TODO: Bruh your forgot to get the better predict from googel collab ;-;

@debug_state.trace_func
def plot(losses, num_points=1000, chop_off=100, sigma=2):
    # Validation
    if len(losses) < chop_off:  # Ensure enough data remains
        raise ValueError("Not enough data points after chopping")
    
    # Remove initial unstable period
    chopped_losses = losses[chop_off:]
    
    # Gaussian smoothing (preserves trends better than moving average)
    smoothed = gaussian_filter1d(chopped_losses, sigma=sigma, mode='nearest')
    
    # Adaptive downsampling - show peaks/valleys while limiting points
    step = max(1, len(smoothed) // num_points)
    sampled_indices = np.arange(0, len(smoothed), step)
    
    # Original batch numbers need adjustment after chopping
    original_batches = np.arange(len(losses))[chop_off:]
    sampled_batches = original_batches[sampled_indices]
    sampled_losses = smoothed[sampled_indices]

    # Plot with improved visualization
    plt.figure(figsize=(12, 6))
    plt.plot(sampled_batches, sampled_losses, 
             linestyle='-', 
             linewidth=1.5,
             color='royalblue',
             alpha=0.8,
             label=f'Smoothed (σ={sigma})')
    
    # Add faint original line for reference
    plt.plot(original_batches, chopped_losses, 
             alpha=0.15, 
             color='gray',
             linewidth=0.5,
             label='Original')
    
    plt.xlabel('Batch', fontsize=12)
    plt.ylabel('Loss', fontsize=12)
    plt.title(f'Loss Curve [First {chop_off} batches chopped]', fontsize=14)
    plt.legend()
    plt.grid(alpha=0.3)
    plt.show()