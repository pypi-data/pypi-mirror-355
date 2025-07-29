from . .common_imports import *
from jax.sharding import Mesh, PartitionSpec as P
from . ._utils import tree_fn, TrainRailGuard
from jax.sharding import NamedSharding
from jax.experimental.pjit import pjit
from . ._utils import val_loss, loss_fn
from tqdm import tqdm
import gc

### Constants
shard_contrain = jax.lax.with_sharding_constraint

class Sharding:
    def __init__(self,shape) -> None:
        devices = np.array(jax.devices()).reshape(shape).transpose((1, 0))
        self.mesh = Mesh(devices, axis_names=('model', 'data'))

    def return_distr(self,x):
        return jax.device_put(x, NamedSharding(self.mesh ,self.get_spec(x)))

    def get_distribution(self,params):
        return tree_fn.apply_tree_fn(params,self.return_distr)
    
    def get_spec(self,x):
        if x.ndim == 1:
            return P('model')
        elif x.ndim == 2:
            return P(None, 'model')
        elif x.ndim == 3:
            return P(None, None, 'model')
        elif x.ndim == 0:
            return P()
        else:
            raise ValueError(f"The init weights contain a dim with {x.ndim} axis and it's still not recognised on which axis to shard")
    
    def get_struct(self,params):
        return tree_fn.apply_tree_fn(params,self.get_spec)
    
    def get_batch_train(self,params,opt_state):
        struct = self.get_struct(params)
        opt_struct = self.get_struct(opt_state)
        def BatchTrain(params, grad_fn, model_struct, x, mask, y, key, optimizer, opt_state):
            loss, grad = grad_fn(params, model_struct, [x,mask,y], key)

            synced_grad = jax.lax.pmean(grad, axis_name='data')

            updates, new_opt_state = optimizer.update(synced_grad, opt_state, params)
            new_params = optax.apply_updates(params, updates)

            return loss, new_params, new_opt_state
        
        return pjit(
            BatchTrain,
            in_shardings=(
                struct,
                P('data',None),
                P('data',None),
                P('data',None),
                None,
                opt_struct
            ),
            out_shardings=(None,struct, opt_struct),
            static_argnums=(1, 2, 7),
            donate_argnums=(0,8)
        )
    
    def get_batch_trainV2():
        def BatchTrain(params, grad_fn, model_struct, x, mask, y, key, optimizer, opt_state):
            loss, grad = grad_fn(params, model_struct, [x,mask,y], key)

            updates, new_opt_state = optimizer.update(grad, opt_state, params)
            new_params = optax.apply_updates(params, updates)

            return loss, new_params, new_opt_state
        
        return jax.jit(
            BatchTrain,
            static_argnums=(1, 2, 7),
            donate_argnums=(0,8)
        )

    def get_batch_trainV3():
        def BatchTrain(params, grad_fn, model_struct, x, mask, y, key, optimizer, opt_state, grad_accum=1):
            batch_size, seq_len = x.shape
            microbatch_size = batch_size // grad_accum

            triplet = jax.lax.concatenate([x[:, None, :], mask[:, None, :].astype(x.dtype), y[:, None, :]], dimension=1)
            reshaped = jax.lax.reshape(triplet, (grad_accum, microbatch_size, 3, seq_len))
            data = jax.lax.transpose(reshaped, (0, 2, 1, 3))
            data = shard_contrain(data,P(None, None,'data', None))   #(grad_accum_steps, 3, microbatch, seq_len)

            grad = jax.tree.map(jnp.zeros_like, params)

            def fw_pass(carry,x):
                loss, grad = grad_fn(params, model_struct, x, key)
                carry = jax.tree_util.tree_map(lambda x, y: x + y, grad, carry)
                return carry,loss
            
            grad, loss = jax.lax.scan(fw_pass,grad,data)
            grad = jax.tree_util.tree_map(lambda x: x/grad_accum,grad)
            updates, new_opt_state = optimizer.update(grad, opt_state, params)
            new_params = optax.apply_updates(params, updates)
            return loss.mean(), new_params, new_opt_state
        
        return jax.jit(
            BatchTrain,
            static_argnums=(1, 2, 7, 9),
            donate_argnums=(0,8)
        )

def train_batch(model,BatchTrain,x,mask,y):
    key = model.key_bruh
    loss, model.params, model.optimizer.state = BatchTrain(model.params,model.grad_fn,model.model_struct,x,mask,y,key,model.optimizer.optimizer,model.optimizer.state)
    return loss , [0,0,0]

def train(model,x,mask,y,epochs,batch_size,optimizer,lr,lrf,val_x=None,val_mask=None,val_y=None,val_step=100,updates_in=1,state_path=None,mesh=(1,1)):
    pass
#Sry, No peaking here too :p