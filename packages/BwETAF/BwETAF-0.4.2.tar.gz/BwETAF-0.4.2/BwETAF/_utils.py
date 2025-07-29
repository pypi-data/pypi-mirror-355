from ._errors import *
from .common_imports import *


def time_it(fn, *args,**kwargs):
    t0 = time.time()
    out = fn(*args,**kwargs)
    t1 = time.time()
    return out, t1 - t0


def loss_fn(params, model, batch, rng,chunks):
    inputs, mask, f_targets = batch

    block_op = model.apply(
        params,
        inputs,
        mask,
        rngs={'dropout': rng},
        method=model.blocks
    )
    b,s,d = block_op.shape
    assert b % chunks == 0, "Batch size must be divisible by chunks!"
    block_op = jax.lax.reshape(block_op,(chunks,b//chunks,s,d))
    b,s = f_targets.shape
    f_targets = jax.lax.reshape(f_targets,(chunks,b//chunks,s))
    dtype = block_op.dtype

    cum_loss = jnp.array(0.0,dtype=jnp.float32)
    for c_chunk in range(chunks):
        c_block_op = jax.lax.index_in_dim(block_op, c_chunk, axis=0, keepdims=False)
        logits = model.apply(params,c_block_op,method=model.last_layer)
        logits = logits.astype(jnp.float32)
        targets = jax.lax.index_in_dim(f_targets, c_chunk, axis=0, keepdims=False)
        shifted_logits = logits[:, :-1, :]  # (B, T-1, C)
        shifted_targets = targets[:, 1:]    # (B, T-1)
        cum_loss += optax.softmax_cross_entropy_with_integer_labels(shifted_logits, shifted_targets).mean()
    return (cum_loss/chunks).astype(dtype)



def grad_trans(grad):
    return grad


@partial(jax.pmap,
        in_axes=(None,None,None,0,0,0,None,None),
        static_broadcasted_argnums=(1,2,7),
        axis_name='batch'
        )
@partial(jax.jit,
        static_argnums=(1,2,7)
        )
def val_loss(params, loss_fn, model_struct, x,mask,y, key,chunks):
    return loss_fn(params, model_struct, [x,mask,y], key,chunks)


# Main training step

def BatchTrain_retired(params, grad_fn, model_struct, x, mask, y, key, optimizer, opt_state):
    pass
#Sry no peaking :p


@partial(jax.pmap,
        static_broadcasted_argnums=(1, 2, 7, 9),
        in_axes=(None, None, None, 0, 0, 0, None, None, None, None),
        axis_name="batch",
        out_axes=None
        )
@partial(jax.jit,
        static_argnums=(1, 2, 7, 9),
        donate_argnums=(0,3,4,5,6,8)
        )
def BatchTrain(params, grad_fn, model_struct, x, mask, y, key, optimizer, opt_state,chunks):
    pass
#Sry no peaking :p
#Some sharding stuff

def get_P_representation(num):         # This function is working but not in use anymore
    args = [None] * (num - 1) + ['model']
    return P(*args)

def is_inside_mesh():
    try:
        mesh = jax.sharding.get_current_mesh()
        return mesh is not None
    except Exception:
        return False

def lax_matmul(V1,V2,cr1,cr2,b,sharding_specs=None):
    if is_inside_mesh() and sharding_specs is not None:
        V1 = jax.lax.with_sharding_constraint(V1, sharding_specs[0])
        V2 = jax.lax.with_sharding_constraint(V2, sharding_specs[1])

    dimension_numbers = (
            (cr1, cr2),
            (b, b)
        )
    return jax.lax.dot_general(V1, V2, dimension_numbers)

# Pytree functions
class tree_fn():
    def get_first(pytree):
        return jax.tree_util.tree_map(lambda x: x[0], pytree)

    def convert_tree(dtype,pytree):
        return jax.tree_util.tree_map(lambda x: x.astype(dtype),pytree)

    def pytree_dtype(pytree):
        return jax.tree_util.tree_leaves(pytree)[0].dtype
    
    def shapes(pytree):
        return jax.tree_util.tree_map(lambda x: x.shape,pytree)
    
    def check_for_nan(pytree):
        def has_nan(x):
            return jnp.isnan(x).any()

        nans = jax.tree_util.tree_map(has_nan, pytree)
        flat_nans = jax.tree_util.tree_flatten(nans)[0]
        return any(flat_nans)   

    def flatten_tree(grads):
        flat_grads = jax.tree_util.tree_leaves(grads)
        all_values = [g.ravel() for g in flat_grads if g is not None]
        return jnp.concatenate(all_values)
    
    def apply_tree_fn(tree,func):
        return jax.tree_util.tree_map(lambda x:func(x),tree)
    
    def avg_trees(tree1, tree2):
        return jax.tree_util.tree_map(lambda a, b: (a + b) / 2, tree1, tree2)
    

class KeyManager:
    def __init__(self, seed=42):
        self.key = jax.random.PRNGKey(seed)

    def next_key(self):
        self.key, subkey = jax.random.split(self.key)
        return subkey

key = KeyManager()             # Constant here too

def get_hlo(func,*args,**kwargs):
    lowered = jax.jit(func).lower(*args,**kwargs)

    compiled = lowered.compile()

    with open("result.hlo", "w") as f:
        f.write(compiled.as_text())
    

class TrainRailGuard:
    def __init__(self,func_cp,least_drop_cp=1.5,critical_stop=3) -> None:
        self.tick = 0
        self.prev_loss = None
        self.least_drop_cp = least_drop_cp
        self.func_cp = func_cp
        self.critical_stop = critical_stop
        self.x = "CONFIRM"
        self.guard = True
        self.cp_num = 0
    
    def check_loss(self,loss):
        if self.prev_loss is None and self.guard:
            pass
        else:
            diff = abs(self.prev_loss - loss)
            if diff > self.least_drop_cp:
                print("Checkpointing because major loss functuation decteted")
                self.func_cp(f"safe_checkpoint{self.cp_num}")
                self.cp_num = self.cp_num + 1
            if diff > self.critical_stop:
                x = input("Critical loss drop dictected, Waiting for user confimation to continue(Continue): ")
                if x == "Continue":
                    self.guard = False

        self.prev_loss = loss

    def lr_check(self,lr,lrf,min_lr=5e-6):
        if lr < lrf:
            print("The final lr is greater! Hope you are in warmup")
        print(f"the learning rate drop is {lr-lrf}")
        if (lr < min_lr) or (lrf < min_lr):
            input("Lr is too low for the model to learn anything... Waiting for user command to continue: ")
            