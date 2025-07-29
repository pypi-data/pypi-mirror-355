from concurrent.futures import ThreadPoolExecutor
from._errors import *
from ._utils import *
from .common_imports import *
from ._utils import is_inside_mesh

shard_contrain = jax.lax.with_sharding_constraint


class Debugger():
    def __init__(self,debug = False,path=None) -> None:
        self.debug = debug
        self.path = path
        if path is not None:
            self.logfile = open(path, "a")
    
    def turn_debugger_on(self):
        self.debug = True
        self.logfile = open(self.path, "a")

    def logger(self,message,state="DEBUG"):
        if self.debug:
            if self.path is None:
                print(f"[{state}] {message}")
            else:
                self.logfile.write(f"[{state}] {message}\n")
                self.logfile.flush()
    
    def Alert(self,message):
        print(f"[WARNING] {message}")
        self.logger(message,state="WARNING")

    def trace_func(self,func):
        def wrapper(*args, **kwargs):
            self.logger(f"Calling {func.__name__} with args: {[type(i) for i in args]}, kwargs: {[type(i) for i in kwargs]} Shapes: {[getattr(i, 'shape', 'uk') for i in args]}",state="FUNC_CALL")
            start_time = time.time()
            try:
                out = func(*args, **kwargs)
            except Exception as e:
                self.logger(f"{func.__name__} Exception:{e}",state="ERROR")
                self.logger(traceback.format_exc(), state="TRACEBACK")
                raise
            name = f"{args[0].__class__.__name__}.__init__" if func.__name__ == "__init__" else func.__name__
            self.logger(f"{name} returned: {type(out)} with shape/info: {getattr(out, 'shape', 'uk')}, {getattr(out, 'dtype', 'uk')}, Time taken:{time.time()-start_time}s",state="FUNC_RETURN")
            return out
        return wrapper

debug_state = Debugger()


class Tokenization():
    @debug_state.trace_func
    def __init__(self,vocab="gpt2") -> None:
        import tiktoken
        self.stuff = tiktoken
        self.vocab = vocab
        self.enc = tiktoken.get_encoding(self.vocab)
        self.pad_token = self.eos_token = 50256

    @debug_state.trace_func
    def tokenize(self,batch:list, workers:int, max_length:int):
        self.enc = self.stuff.get_encoding(self.vocab)
        enc = self.enc

        def encode_and_pad(text):
            tokens = enc.encode(text, allowed_special={'<|endoftext|>'})[:max_length]
            padded = np.full(max_length, self.pad_token, dtype=np.int32)
            mask = np.zeros(max_length, dtype=np.int32)
            padded[:len(tokens)] = tokens
            mask[:len(tokens)] = 1  # Mark real tokens as 1
            return padded, mask
        
        with ThreadPoolExecutor(max_workers=workers) as executor:
            results = list(executor.map(encode_and_pad, batch))
        
        encoded_batch, mask = zip(*results)  # Split tokens and masks
        encoded_batch = np.array(encoded_batch)
        mask = np.array(mask)
        
        return encoded_batch, mask

    @debug_state.trace_func
    def tokenize_max_util(self,data,workers,max_length):
        self.enc = self.stuff.get_encoding(self.vocab)
        enc = self.enc

        def encode(text):
            tokens = enc.encode(text, allowed_special={'<|endoftext|>'})
            return tokens
        
        def last_one(tokens):
            padded = np.full(max_length, self.pad_token, dtype=np.int32)
            mask = np.zeros(max_length, dtype=np.int32)
            padded[:len(tokens)] = tokens
            mask[:len(tokens)] = 1  # Mark real tokens as 1
            return padded, mask
        
        with ThreadPoolExecutor(max_workers=workers) as executor:
            results = list(executor.map(encode, data))

        chain = []
        take = chain.append
        for i in results:
            take(i)
            if chain[-1][-1] != self.eos_token:
                take([self.eos_token])

        chain = np.concatenate(chain)
        content = [chain[i:i+max_length] for i in range(0,len(chain),max_length)]
        content = np.array(content[:-1])
        mask = np.ones(content.shape, dtype=np.int32)
        last_sentence,last_mask = last_one(content[-1])
        last_sentence,last_mask = last_sentence.reshape(1,max_length),last_mask.reshape(1,max_length)
        input = np.concatenate((content,last_sentence),axis=0)
        mask = np.concatenate((mask,last_mask),axis=0)
        return input, mask


    @debug_state.trace_func
    def tokenize_(self, batch: list):
        self.enc = self.stuff.get_encoding(self.vocab)
        enc = self.enc

        encoded_batch = []
        mask = []

        for text in batch:
            tokens = enc.encode(text, allowed_special={'<|endoftext|>'})
            encoded_batch.append(np.array(tokens, dtype=np.int32))
            mask.append(np.ones(len(tokens), dtype=np.int32))  # Mask matches token length
        
        return jnp.array(encoded_batch), jnp.array(mask)
    
    @debug_state.trace_func
    def decode(self,tokens):
        return self.enc.decode(tokens)
    
class Flax_ds():
    @debug_state.trace_func
    def __init__(self,x_eq_y:bool) -> None:
        self.x_eq_y = x_eq_y
        self.x = None
        self.mask = None
        self.y = None
        self.batch = None
    
    @debug_state.trace_func
    def load_data(self,x,mask,y):
        self.x = np.array(x)
        self.mask = mask
        if not self.x_eq_y:
            self.y = np.array(y)
    
    @debug_state.trace_func
    def batch_it_(self,batch_size):
        if not self.x_eq_y:
            self.seq_len = self.x.shape[1]
            
            n_batches = len(self.x) // batch_size
            num_devices = jax.device_count()
            
            self.x_batch = [self.x[i * batch_size:(i + 1) * batch_size] for i in range(n_batches)]
            self.mask_batch = [self.mask[i * batch_size:(i + 1) * batch_size] for i in range(n_batches)]
            self.y_batch = [self.y[i * batch_size:(i + 1) * batch_size] for i in range(n_batches)]
            
            
            self.batch = [[i.reshape(num_devices,-1, self.seq_len), j.reshape(num_devices,-1, self.seq_len), k.reshape(num_devices,-1, self.seq_len)] for i, j, k in zip(self.x_batch, self.mask_batch, self.y_batch)]

            del self.x, self.mask, self.y
            return self.batch
        
        else:
            self.seq_len = self.x.shape[1]
            
            n_batches = len(self.x) // batch_size
            num_devices = jax.device_count()
            
            self.x_batch = [self.x[i * batch_size:(i + 1) * batch_size] for i in range(n_batches)]
            self.mask_batch = [self.mask[i * batch_size:(i + 1) * batch_size] for i in range(n_batches)]
            
            
            self.batch = [[i.reshape(num_devices,-1, self.seq_len), j.reshape(num_devices,-1, self.seq_len)] for i, j in zip(self.x_batch, self.mask_batch)]

            del self.x, self.mask
            return self.batch
        
    
    def __len__(self):
        return len(self.batch)

    def stream_it(self):
        if self.batch == None:
            IncorrectDtype("Bruh... You forgot to run '.batch_it' before trying to stream it.... T~T")
        if self.x_eq_y:
            for i in self.batch:
                x = jnp.array(i[0],dtype=jnp.uint16)
                yield x,jnp.array(i[1],dtype=jnp.uint8),x
        else:
            for i in self.batch:
                yield jnp.array(i[0],dtype=jnp.uint16),jnp.array(i[1],dtype=jnp.uint8),jnp.array(i[2],dtype=jnp.uint16)
        
    def stream_it_dir(self):
        if not is_inside_mesh:
            raise ValueError("This function is suppose to work only within a mesh")
        if not self.x_eq_y:
            self.batch = [[i.reshape(-1, self.seq_len), j.reshape(-1, self.seq_len), k.reshape(-1, self.seq_len)] for i, j, k in zip(self.x_batch, self.mask_batch, self.y_batch)]
            for i in self.batch:
                yield shard_contrain(i[0],P('data',None)).astype(jnp.uint16), shard_contrain(i[1],P('data',None)).astype(jnp.uint8), shard_contrain(i[2],P('data',None)).astype(jnp.uint16)
        
        else:
            self.batch = [[i.reshape(-1, self.seq_len), j.reshape(-1, self.seq_len)] for i, j in zip(self.x_batch, self.mask_batch)]
            for i in self.batch:
                x = shard_contrain(i[0],P('data',None)).astype(jnp.uint16)
                yield x, shard_contrain(i[1],P('data',None)).astype(jnp.uint8), x
    
    @property
    def gimme_the_data(self):
        return self.batch
    
class Optimizer():
    @debug_state.trace_func
    def __init__(self,optimizer,lr,lrf,batches,epochs,params,dtype):
        decay_rate = (lrf / lr) ** (1 / (batches * epochs))
        self.lr_schedule = optax.exponential_decay(
            init_value=lr,
            transition_steps=1,
            decay_rate=decay_rate,
            staircase=False  # Smooth decay
        )
        self.optimizer = optimizer(self.lr_schedule)
        self.state = self.optimizer.init(params)
        if dtype is not None:
            print("The optimizer is in:",tree_fn.pytree_dtype(self.state))
    
    @debug_state.trace_func
    def load(self,path,dtype=None):
        try:
            with open(os.path.join(path, "make_stuff_better.pkl"), "rb") as f:
                self.state = flax.serialization.from_bytes(self.state, f.read())
                if dtype is not None:
                    self.state = tree_fn.convert_tree(dtype,self.state) 
                print("Using loaded optimizer states")
        except:
            print("No optimizers states found")

    @debug_state.trace_func
    def save(self,path):
        os.makedirs(path, exist_ok=True)
        with open(os.path.join(path, "make_stuff_better.pkl"), "wb") as f:
            f.write(flax.serialization.to_bytes(self.state))

