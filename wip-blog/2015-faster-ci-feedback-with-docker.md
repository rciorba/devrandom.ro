Faster CI feedback, with Docker
===============================
_soundtrack: Samsara Blues Experiment - Long Distance Trip_

Fast Feedback
-------------
At LM we like to know if a Pull Request breaks any tests before merging it.
Gitub has an extremly simple api for this, so getting it setup has been a breeze, however
as our app became more complex, build times started to suffer. Soon enough the tests were
running slow enough that most of the time someone would review a PR they'd do so without
waiting for the tests to finish.

Slow Tests or Slow Setup?
-------------------------
A quick glance at what is causing the pain, and we can see we spend most of our time
installing dependencies. The worst offenders are python C extensions that require compilation
(lxml, mysql) and the node/bower madness that seems to download the internet several times
over.

Cache?
------
Pip is now nice enough to build and cache wheels of the 3rd party dependencies you install,
and node keeps a node_modules directory so it doesn't have to re-download everything, however
since our CI agents are efemeral VMs this doesn't really do much for us.

Enter Docker
------------
If you're unfamiliar with Docker, there are many great articles explaining what it does and
why it's awesome at. For our needs we'll think of it as a way to quickly and cheeply build
a sort of light weight VMs* that will capture our external dependencies.

*Ok, so they're not VMs, they're containers, "chroots on steroids" that run in a separate
filesystem/process/network namespace, but share a kernel with the host. You don't really "boot"
one up, it's more like runing a process in isolation.

The Plan
--------
Since the slow bit for us is gathering and installing the dependencies, what if we could
somehow snapshot environments, and re-use them unless our dependencies have changed?
Well, with docker you can "snapshot" a machine image and share it.
The code itself won't be part of the image, but will get bind mounted in to the container,
that way we only need to rebuild the image if we add a new dependency or change a version
(we have pinned versions, if you don't you're a bad person and should feel bad).

Let's go ahead and identify what files define our dependencies, then we can get a hash of those
to use as a tag. In our case it's our REQUIREMENTS / REQUIREMENTS.dev files plus about 3 node
package.json and bower.json files. Yes, there's 3 of them because FML...

Context. No, literally docker build context
-------------------------------------------
Docker makes files in your current directory available for embeding in the target image,
but since our repo has brown huge over the years and the client-server nature of docker means
this context needs to be uploaded to the daemon, I chose to simply create a directory with
as little stuff as necesary to build the image.

Here's the script I use to calculate the hash that identifies our dependencies image:

    #!/bin/bash
    
    rm -rf dependencies
    mkdir dependencies

    # copy required files into subdirectory to keep context small
    cp ../package.json ./dependencies/
    mkdir ./dependencies/caesar/
    cp ../apps/caesar/caesar/static/poster/package.json ./dependencies/caesar/
    cp ../apps/caesar/caesar/static/poster/bower.json ./dependencies/caesar/
    mkdir ./dependencies/brutus
    cp ../apps/brutus/brutus/static/brutus/package.json ./dependencies/brutus/
    cp ../apps/brutus/brutus/static/brutus/bower.json ./dependencies/brutus/
    
    cp ../learning_media/REQUIREMENTS ./dependencies/
    cp ../learning_media/REQUIREMENTS.dev ./dependencies/
    
    declare -a DEPENDENCIES=("package.json" "caesar/package.json" "caesar/bower.json" "brutus/package.json" "brutus/bower.json" "REQUIREMENTS" "REQUIREMENTS.dev")
    
    REQUIREMENTS=""
    for dep in "${DEPENDENCIES[@]}"; do
        REQUIREMENTS=$REQUIREMENTS"$( shasum ./dependencies/$dep | cut -f 1 -d ' ' )";
    done
    REQUIREMENTS="$( echo $REQUIREMENTS | shasum | cut -f 1 -d ' ' )"

