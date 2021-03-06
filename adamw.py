import torch
import math
from torch.optim.optimizer import Optimizer

class AdamW(Optimizer):
  def __init__(self,params,lr=1e-3,betas=(0.9,0.999),eps=1e-8,weight_decay=0,amsgrad=False):
    if not lr >= 0.0:
      raise ValueError("Learning rate invalid:{}".format(lr))
    if not eps >= 0.0:
      raise ValueError("Epsilon invalid:{}".format(eps))
    if not 0.0 <= betas[0] < 1.0:
      raise ValueError("Beta parameter invalid at index 0:{}".format(betas[0]))
    if not 0.0 <= betas[1] < 1.0:
      raise ValueError("Beta parameter invalid at index 1:{}".format(betas[1]))
    
    defaults=dict(lr=lr,betas=betas,eps=eps,weight_decay=weight_decay,amsgrad=amsgrad)
    super(AdamW,self).__init__(params,defaults)
    
  def __setstate__(self,state):
    super(AdamW,self).__setstate__(state)
    for group in self.param_groups:
      group.setdefault('amsgrad',False)
      
  def step(self, closure=None):
    loss=None
    if closure is not None:
      loss=closure()
      
    for group in self.param_groups:
      for p in group['params']:
        if p.grad is None:
          continue
        grad=p.grad.data
        if grad.is_sparse:
          raise RuntimeError('AdamW does not support sparse gradients,please consider SparseAdamW instead')
        amsgrad=group['amsgrad'] 
        state =self.state[p]
        
        if len(state) == 0:
          state['step'] = 0
          state['exp_avg']=torch.zeros_like(p.data)
          state['exp_avg_sq']=torch.zeros_like(p.data)
          if amsgrad:
            state['max_exp_avg_sq']=torch.zeros_like(p.data)
            
        exp_avg,exp_avg_sq=state['exp_avg'],state['exp_avg_sq']
        if amsgrad:
          max_exp_avg_sq=state['max_exp_avg_sq']
        
        beta1,beta2=group['betas']
        state['step']+=1
        exp_avg.mul_(beta1).add_(1-beta1,grad)
        exp_avg_sq.mul_(beta2).add_(1-beta2,grad**2)
        if amsgrad:
          torch.max(exp_avg_sq,max_exp_avg_sq,out=max_exp_avg_sq)
          denom=max_exp_avg_sq.sqrt().add_(group['eps'])
        else:
          denom=exp_avg_sq.sqrt().add_(group['eps'])
          
        bias_correction1=1-beta1**state['step']
        bias_correction2=1-beta2**state['step']
        
        step_size=group['lr']*math.sqrt(bias_correction2)/bias_correction1
        
        p.data.add_(-step_size,torch.mul(p.data,group['weight_decay']).addcdiv_(1,exp_avg,denom))
          
          
    return loss

