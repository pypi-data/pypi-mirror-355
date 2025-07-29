from typing import Any
from . .common_imports import *
from . ._utils import lax_matmul
from jax import lax
from flash_attention_jax import flash_attention
from . ._errors import ModelHpMismatch, UnusableModule


class PosEnc(nn.Module):
    dim : int
    dtype: jnp.dtype = jnp.bfloat16

    @nn.compact
    def __call__(self, x):
        _ , sequence_length, _ = x.shape  

        # Compute div term once (avoiding repeated `exp` calls)
        div_term = jnp.exp(-jnp.arange(0, self.dim, 2) * (jnp.log(10000.0) / self.dim)).astype(self.dtype)

        # Compute positions in one step (efficiently broadcasting)
        position = jnp.arange(sequence_length)[:, None] * div_term  # (seq_len, emb_dim/2)

        # Directly compute sine & cosine, then interleave them
        pos_enc = jnp.zeros((sequence_length, self.dim),dtype=self.dtype)
        pos_enc = pos_enc.at[:, 0::2].set(jnp.sin(position)).astype(self.dtype)
        pos_enc = pos_enc.at[:, 1::2].set(jnp.cos(position)).astype(self.dtype)

        # Expand for batch & return
        return x + pos_enc[None, :, :]

def rotate_half(x):
    x1, x2 = jnp.split(x, 2, axis=-1)
    return jnp.concatenate([-x2, x1], axis=-1)

def RoPE(embeddings,*args,**kwargs):
    batch_size, seq_len, hidden_dim = embeddings.shape
    assert hidden_dim % 2 == 0, "hidden_dim must be even"
    
    # Generate position IDs (0 to seq_len-1)
    pos_ids = jnp.arange(seq_len, dtype=jnp.float32)[None, :]  # [1, seq_len]
    
    # Calculate rotation frequencies
    dim_idx = jnp.arange(hidden_dim//2, dtype=jnp.float32)
    freqs = 1.0 / (10000 ** (2 * dim_idx / hidden_dim))
    
    # Compute angles for all positions and dimensions
    angles = jnp.einsum("bi,j->bij", pos_ids, freqs)  # [1, seq_len, dim//2]
    
    # Compute cos and sin values
    cos = jnp.cos(angles)
    sin = jnp.sin(angles)
    
    # Interleave cos/sin values to match hidden_dim
    cos = jnp.repeat(cos, 2, axis=-1)  # [1, seq_len, hidden_dim]
    sin = jnp.repeat(sin, 2, axis=-1)  # [1, seq_len, hidden_dim]
    
    # Apply rotation to embeddings
    rotated_embeddings = embeddings * cos + rotate_half(embeddings) * sin
    return rotated_embeddings

class Attention(nn.Module):
    num_heads: int
    d_model: int
    dtype: jnp.dtype = jnp.bfloat16

    def setup(self):
        if self.d_model % self.num_heads != 0:
            raise ModelHpMismatch("d_model must be divisible by num_heads")
        self.depth = self.d_model // self.num_heads
        self.k_dense = lax_Dense(features=self.d_model, dtype=self.dtype,use_bias=False)
        self.q_dense = lax_Dense(features=self.d_model, dtype=self.dtype,use_bias=False)
        self.v_dense = lax_Dense(features=self.d_model, dtype=self.dtype,use_bias=False)
        self.d_out = lax_Dense(features=self.d_model,dtype=self.dtype)

    def __call__(self, x, mask):
        batch_size, seq_len, _ = x.shape

        q = jax.lax.transpose(self.q_dense(x).reshape(batch_size, seq_len, self.num_heads, self.depth), (0, 2, 1, 3))
        k = jax.lax.transpose(self.k_dense(x).reshape(batch_size, seq_len, self.num_heads, self.depth), (0, 2, 1, 3))
        v = jax.lax.transpose(self.v_dense(x).reshape(batch_size, seq_len, self.num_heads, self.depth), (0, 2, 1, 3))

        logits = lax_matmul(q,k,(3,),(3,),(0,1),(P("data", "model", None, None),P("data", "model", None, None))) /jnp.sqrt(self.depth)

        logits = jnp.where(mask, logits, -1e9)

        attn_weights = jax.nn.softmax(logits, axis=-1)
        attn_output = lax_matmul(attn_weights, v, (3,), (2,), (0, 1),(P("data", "model", None, None),P("data", "model", None, None)))

        # Concatenate heads
        attn_output = lax.transpose(attn_output, (0, 2, 1, 3))  # (batch, seq_len, num_heads, depth)
        concat_output = lax.reshape(attn_output,(batch_size, seq_len, self.d_model))  # (batch, seq_len, d_model)

        return self.d_out(concat_output)

class FlashAttentionLayer(nn.Module):
    num_heads: int
    d_model: int
    dtype: jnp.dtype = jnp.bfloat16

    def setup(self):
        assert self.d_model % self.num_heads == 0, "d_model must be divisible by num_heads"
        self.depth = self.d_model // self.num_heads
        self.k_dense = lax_Dense(features=self.d_model, dtype=self.dtype,use_bias=False)
        self.q_dense = lax_Dense(features=self.d_model, dtype=self.dtype,use_bias=False)
        self.v_dense = lax_Dense(features=self.d_model, dtype=self.dtype,use_bias=False)
        self.d_out = lax_Dense(features=self.d_model,dtype=self.dtype)

    def __call__(self, x, mask):
        raise UnusableModule("The model which you are using has a unusable flash attention with correpted masking.. Please consider using the normal attention for now")
        batch_size, seq_len, _ = x.shape

        q = lax.reshape(self.q_dense(x).astype(jnp.float32), (batch_size, self.num_heads,seq_len , self.depth))
        k = lax.reshape(self.k_dense(x).astype(jnp.float32), (batch_size, self.num_heads,seq_len , self.depth))
        v = lax.reshape(self.v_dense(x).astype(jnp.float32), (batch_size, self.num_heads,seq_len , self.depth))
        attn_weights = flash_attention(q, k, v, mask).astype(jnp.bfloat16)

        attn_weights = lax.transpose(attn_weights, (0, 2, 1, 3)) # (batch, seq_len, num_heads, depth)
        attn_weights = lax.reshape(attn_weights,(batch_size, seq_len, self.d_model)) # (batch, seq_len, d_model)
        return self.d_out(attn_weights)
    

def softmax_lax(x, axis=-1):
    x_max = lax.max(x, axes=(axis,), keepdims=True)
    x = lax.sub(x, lax.stop_gradient(x_max))  # for numerical stability
    exp_x = lax.exp(x)
    sum_exp_x = lax.reduce(exp_x, 0.0, lax.add, axes=(axis,), keepdims=True)
    return lax.div(exp_x, sum_exp_x)


class Block(nn.Module):
    num_heads : int
    attention_dim : int
    ff_dim : int
    dropout_rate : float
    flash_attn: bool = False
    dtype: jnp.dtype = jnp.bfloat16

    def setup(self):
        self.ln1 = nn.LayerNorm(dtype=self.dtype)
        self.attn = nn.remat(Attention)(self.num_heads, self.attention_dim,dtype=self.dtype)
        self.dp1 = nn.Dropout(self.dropout_rate)
        self.ln2 = nn.LayerNorm(dtype=self.dtype)
        self.d1 = lax_Dense(self.ff_dim*2, dtype=self.dtype,use_bias=False)
        self.d2 = lax_Dense(self.attention_dim, dtype=self.dtype)

        
    def __call__(self, x_inp, mask, train=True):
        x = self.ln1(x_inp)  
        x = self.attn(x, mask)
        x = self.dp1(x, deterministic=not train)
        x_inp = x + x_inp

        # Pre-LN before FFN
        x = self.ln2(x_inp)  
        x = self.d1(x)
        key, gate = jnp.split(x, 2, axis=-1)
        x = self.d2(nn.swish(gate) * key)
        return x + x_inp



class lax_Dense(nn.Module):
    features : int
    dtype: jnp.dtype = jnp.bfloat16
    use_bias: bool = True

    @nn.compact
    def __call__(self,x) -> Any:
        w = self.param('w',nn.initializers.normal(stddev=0.02),(x.shape[-1],self.features),dtype=self.dtype)
        if self.use_bias:
            b = self.param('b', nn.initializers.zeros, (1, 1, self.features), dtype=self.dtype)

        if self.use_bias:
            return jax.lax.add(lax_matmul(x,w,(2),(0),()),b)
        else:
            return lax_matmul(x,w,(2),(0),())
    

class FactorizedEmbed(nn.Module):  # TODO: Do something about this.... I don't think it's gonna make it so break it like not handled sharding specs
    vocab_size: int
    embed_dim: int
    factor_dim: int = 0
    dtype: jnp.dtype = jnp.bfloat16

    def setup(self):
        raise UnusableModule("The FactorizedEmbed layer is still underdevelopment and might break under certain conditions... Use at your own risk")
        if self.factor_dim == 0:
            self.embed_factor = nn.Embed(self.vocab_size, self.embed_dim,dtype=self.dtype)
        else:
            self.embed_factor = nn.Embed(self.vocab_size, self.factor_dim,dtype=self.dtype)
            self.P_w = self.param('w',nn.initializers.normal(stddev=0.02),(self.factor_dim,self.embed_dim),dtype=self.dtype)

    def __call__(self, x):
        if self.factor_dim == 0:
            return self.embed_factor(x)
        else:
            x = self.embed_factor(x)
            return lax_matmul(x,self.P_w,(2),(0),())
    
    def rev_call(self,x):
        if self.factor_dim == 0:
            return lax_matmul(x, self.embed_factor.embedding, (2,), (1,),())
        else:
            x = lax_matmul(x,self.P_w,(2),(1),())
            return lax_matmul(x, self.embed_factor.embedding, (2,), (1,),())
    