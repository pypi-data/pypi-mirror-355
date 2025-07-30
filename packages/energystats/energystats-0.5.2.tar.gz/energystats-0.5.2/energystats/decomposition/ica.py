import numpy as np
import scipy.linalg as la
from energystats.tests.cor import multi_fast_dcov, dcov, _dcov_grad_x_vec as _dcov_grad

def dcov_single(X, fast = 1):
    fun = multi_fast_dcov if fast else dcov
    return fun(X[:,0,None], X[:,1:])

def grad_single(X):
    gx,gY = _dcov_grad(X[:,0], X[:,1:])
    G = np.zeros_like(X)
    G[:,0] = gx
    G[:,1:]= gY
    return G

def givens(t,d,p,q):
    G = np.eye(d); c,s=np.cos(t),np.sin(t)
    G[p,p] = G[q,q] =c
    G[p,q] = -s
    G[q,p] = s
    return G

def rotation(T):
    d = T.shape[0]; W = np.eye(d)
    for i in range(d-1):
        for j in range(i+1,d):
            W=W@givens(T[i,j],d,i,j)
    return W
def unpack_theta(v,d):
    T=np.zeros((d,d)); T[np.triu_indices(d,1)]=v; return T

def gradient_descent(grad, theta0, Z, tol=1e-5, max_iter=100):
    alpha = 0.7
    for i in range(max_iter):
        grad_val = grad(theta0, Z)
        theta_new = theta0 - alpha * grad_val
        if np.linalg.norm(theta_new - theta0) < tol:
            break
        theta0 = theta_new
        alpha *= 0.95  
    return theta0    

def obj(theta, Z):
    d=Z.shape[1]; S=Z@rotation(unpack_theta(theta,d)).T
    return sum(dcov_single(S[:,i:]) for i in range(d-1))

def grad_theta(theta, Z):
    d=Z.shape[1]; T=unpack_theta(theta,d)
    pairs=[(i,j) for i in range(d-1) for j in range(i+1,d)]
    prefix=[np.eye(d)]
    for (i,j) in pairs: prefix.append(prefix[-1]@givens(T[i,j],d,i,j))
    suffix=[np.eye(d)]
    for (i,j) in reversed(pairs): suffix.append(givens(T[i,j],d,i,j)@suffix[-1])
    suffix=list(reversed(suffix))
    W=prefix[-1]; S=Z@W.T
    GS=np.zeros_like(S)
    for i in range(d-1): GS[:,i:]+=grad_single(S[:,i:])
    GW=GS.T@Z
    g=[]
    for k,(i,j) in enumerate(pairs):
        A=prefix[k]; B=suffix[k+1]
        c,s=np.cos(T[i,j]),np.sin(T[i,j])
        dW=np.zeros((d,d)); dW[np.ix_([i,j],[i,j])]=np.array([[-s,-c],[c,-s]])
        g.append(np.sum(GW*(A@dW@B)))
    return np.array(g)

def dCovICA(Y, starts=1000, **kwargs):
    mean=Y.mean(0); Z=(Y-mean)@la.sqrtm(np.linalg.inv(np.cov(Y-mean,rowvar=False))).real.T
    d=Z.shape[1]; p=d*(d-1)//2
    best=np.inf; best_theta=None
    print(Y.shape)
    for _ in range(starts):
        th0=np.random.uniform(-np.pi,np.pi,p)
        res=gradient_descent(grad_theta, th0, Z, tol = kwargs.get('tol', 1e-5), max_iter=kwargs.get('max_iter', 50))
        val_res = obj(res, Z)
        if val_res<best:
            best,res_theta=val_res,res
            best_theta=res_theta
    S = Z@rotation(unpack_theta(best_theta,d)).T
    return rotation(unpack_theta(best_theta,d)).T, S-S.mean(0)

