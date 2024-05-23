import dask.array as da
from dask import delayed
from wukong import LocalCluster, Client

# Automatically resolve private ipv4.
# You can set this manually if preferred/necessary.
import socket 
hostname = socket.getfqdn()
private_ipv4 = socket.gethostbyname_ex(hostname)[2][0]

local_cluster = LocalCluster(
    host=private_ipv4, 
    proxy_address=private_ipv4, 
    num_lambda_invokers = 2, 
    use_local_proxy = False, 
    redis_endpoints = [(private_ipv4, 6379)], 
    use_fargate = False)
client = Client(local_cluster)

def incr(x):
    return x + 1

example_computation = delayed(incr)(5)

result = example_computation.compute(scheduler = client.get)
print("Result: %d" % result)

client.close()
local_cluster.close()