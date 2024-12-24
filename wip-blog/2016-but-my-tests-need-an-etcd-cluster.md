But my tests need and ETCD cluster.
===================================

Do you ever get that feeling that it's not worth writing tests for
some piece of code because the external dependencies are to complex?
Recently I was working on setting up an etcd cluster at Presslabs, and
since the infrastructure is automated with ansible it made sense to
write a plugin to allow us to add and remove servers from the cluster.
My knee-jerk reaction was to avoid writing tests, I mean all you need
to do is write a playbook that uses the plugin and a vagrantfile with
3 machines and you're good, right? Of course as I was implementing it,
I realized all is not simple.

First of all there are different things I want to test and each
require a different cluster state, for example I want a cluster of one
machine to add a second node to it, or I want to have a cluster of 3
machines but with one dead one to ensure I can't add another node
before removing the dead node from the cluster, and it sure would be
convenient if I could spin up such a cluster any time I needed one.
After a couple of hours of constantly bringing my cluster to a certain
state, then waiting for ansible to run my playbook I decided I'm
wasting time by NOT writing automated tests.

Docker to the rescue.
=====================

Using Docker and the docker-py api I was able to write a pytest
fixture that would provide me with the desired cluster at the start of
each test. Now my feedback loop has been reduced to a few seconds if
I'm only testing one feature as I'm working on it, or just under a
minute to ensure I haven't broken other features while implementing
the current one, and that is IMHO the biggest value we get from TDD,
the fast feedback loop.

Why docker? The beauty of using docker's api is you start programs in
isolation, stream program output, ensure propper cleanup and more, all
with a simple and elegant api.

A word on etcd
==============

Before diving in to the code, first a few things about etcd. We're
dealing with a distributed key-value store with high emphasis on
consistency, that implements the raft protocol. Consistency is
achieved by getting 50%+1 of members(the quorum) to acknowlegge
changes, for example if you have 3 members, and write a value, it has
to be acknowleged by at least 2 nodes before your write succedes.

Adding and removing members from the cluster is a non-trivial
operation mainly because adding a new member means we could affect the
number of nodes required to achieve quorum whenever we change data.



Developing ansible plugins
==========================

Ansible has a very simple model for plugins, basincally they need to
be executables that write json to stdout. If you decouple argument
handling and output from your business logic, then you can test your
core logic just like you would any other piece of code.


On to the code
==============

The docker api is quite straight forward, and very close to a 1 to 1
match to the docker command line.

First we need to connect to the docker server:

    docker_url = os.getenv('DOCKER_URL', 'unix://var/run/docker.sock')
    docker_image = os.getenv('DOCKER_IMAGE', 'quay.io/coreos/etcd:v2.3.0-alpha.0')
    client = docker.Client(base_url=docker_url, version='auto')

Now let's prepare the list of initial URLs for etcd. When starting a
new etcd cluster you need to tell all nodes about the urls of every
node that will participate in the cluster.

    initial_urls = []
    for i in xrange(count):
        # prepare list of urls, all nodes in the cluster need this when staring up
        p_port = 2380 + i
        initial_urls.append("node{i}=http://127.0.0.1:{p_port}".format(i=i, p_port=p_port))

Now let's define our containers. Notice we use host networking, that
means we don't actually isolate the network stacks of the nodes. I did
this because it was the quickest way to get the nodes to communicate,
but that means I have to ensure each node runs on different ports

    command = ["-name=node{i}",
               "-advertise-client-urls", "http://127.0.0.1:{c_port}",
               "-listen-client-urls", "http://0.0.0.0:{c_port}",
               "-initial-advertise-peer-urls", "http://127.0.0.1:{p_port}",
               "-listen-peer-urls", "http://0.0.0.0:{p_port}",
               "-initial-cluster-token", "etcd-cluster-1",
               "-initial-cluster", ",".join(initial_urls),
               "-initial-cluster-state", "new"]
    cluster = []
    streams = []
    for i in xrange(count):
        container = client.create_container(
            image=docker_image,
            command=[c.format(i=i, c_port=4001+i, p_port=2380+i) for c in command],
            name="node{}".format(i),
            host_config=client.create_host_config(
                network_mode='host',  # all nodes will share the host's ip address
            ),
        )
        cluster.append(EtcdDaemon(
            container, peer_port=2380+i, client_port=4001+i, name="node{}".format(i)))

Now let's hook up our cleanup logic. This would be the equivalent of
the tearDown method if you're familiar with the unittest api:

    def cleanup():
        callbacks = []
        for daemon in cluster:
            c_id = daemon.container.get("Id")
            def callback(c_id=c_id):
                client.stop(c_id, timeout=0.00001)
                client.remove_container(c_id, force=True)
            callbacks.append(callback)
        pool = ThreadPool(count)
        results = [pool.apply_async(cb) for cb in callbacks]
        [res.wait() for res in results]
    request.addfinalizer(cleanup)

Start the containers:

    for daemon in cluster:
        client.start(daemon.container.get("Id"))
        streams.append(StreamHandler(client, daemon.container))

And wait for each node to confirmat that it's up and running:

    for i, stream in enumerate(streams):
        stream.wait(
            re.compile(".* etcdserver: published {{Name:node{} .*".format(i)))
    return client, cluster
