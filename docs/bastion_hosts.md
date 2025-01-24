Dealing with bastion hosts/jumpboxes
====================================

Occasionally, you will not be able to access your Vault hosts directly from the machine you are plugging your YubiKey into. One of the most likely reasons for this is because you need to hop through a bastion host, otherwise known as a jumpbox. Unfortunately this means that you'll need to go through a few more hoops to get this collection up and running.

There are two approaches that can make this work. The first is to configure Ansible to use your bastion host when it executes SSH commands. This is simpler and arguably more secure in the sense that you are not exposing your GPG agent to the remote host. It does, however, have a drawback in that each command will execute considerably slower. _Unless you need to run the playbooks from a shared Ansible control node, this is the approach you should prefer._

The second approach is to forward your GPG agent on to your bastion host, and then on again from there to the machine where you will be running Ansible. This is considerably more complex, and requires configuration on both the client and remote sides to work properly. It also means that the ephemeral GPG agent that this collection sets up by default **will not work**, and you'll need to modify the playbooks appropriately.


Method 1 - SSH jumping
----------------------
WIP

Method 2 - GnuPG agent forwarding
---------------------------------
Before we begin, let's be clear. This is more complex and unreliable than the first method we described above. It requires you to add configuration to the SSH client on your local machine and on the bastion host, and requires modifications to `sshd_config` on the bastion host and Ansible control node. If you do not have root access to both remote machines, this will not work reliably for you. 

Let's begin! We'll assume that you are running macOS on your local machine, and a flavour of Red Hat Enterprise Linux on the remotes. 

### Preparing your local machine
We have found that CLI `pinentry` does not behave when invoked from an Ansible run. Thankfully, a graphical version exists and is available in Homebrew.

    brew install pinentry-mac

The next thing we need to do is find out the path to our GnuPG agent socket. The best practice is to use the "extra" socket, which is better suited for forwarding as it enables the decryption/signing functions, but doesn't expose the private keys to the remote host.

    $ gpgconf --list-dir agent-extra-socket
    /Users/XXXXX/.gnupg/S.gpg-agent.extra

Make note of this, we'll need it in the next step.

Next, we'll set up our SSH configuration to forward the socket file to the bastion host. This involves modifying your `~/.ssh/config` file to add a new `RemoteForward` directive. The first parameter is the desired path on the remote machine, and the second is the path to the socket we found in the previous step.

    Host accessXXX  # Change me as required - you might already have a Host block

	    RemoteForward /home/XXXXX/.gnupg/S.gpg-agent-local /Users/XXXXX/.gnupg/S.gpg-agent.extra

You might notice that I have selected an arbitrary filename in my user's `.gnupg` directory, rather than the typical location of the socket in `/run/user`. In this case I don't necessarily want or need the bastion host to use my forwarded GPG agent. Choosing a unique path therefore limits the potential for confusion in debugging the forwarding.

### Preparing the bastion host
**IMPORTANT:** In order for our forwarded socket to work reliably, we need to set `StreamLocalBindUnlink yes` in `/etc/ssh/sshd_config`. This allows sshd to automatically clean up a stale socket from a previous connection before forwarding on the new one.

Assuming you've set everything up as described above, connecting to your bastion host should now yield you a socket file at the location you chose (e.g. `/home/XXXXX/.gnupg/S.gpg-agent-local`). If this doesn't happen, jump to the troubleshooting section below. You can give this a go to see the forwarding in action.

    gpg-connect-agent -S /home/XXXXX/.gnupg/S.gpg-agent-local

If this command doesn't immediately throw an error, congrats, it's working!

We now need to set up the SSH client config on the bastion host. The first step is to determine the socket on the Ansible control node that we need to forward to. This will ensure that when we call `gpg` from the playbooks, we're actually talking to your forwarded agent.

**On your Ansible control node:**
    
    gpgconf --list-dir agent-socket

Note down the output - it'll probably be something like `/run/user/XXXX/gnupg/S.gpg-agent`.

Next, in `~/.ssh/config` on the **bastion host**:

    Host ansible??? # Again - change the hostname as required!
	    RemoteForward /run/user/XXXX/gnupg/S.gpg-agent /home/XXXXX/.gnupg/S.gpg-agent-local

Pay careful attention to the ordering. The first parameter is the socket path you're creating on the **Ansible control node** - that is, the output of the `gpgconf` command we just did. The second parameter is the path to the forwarded socket on the **bastion host**. 

### Preparing the Ansible control node
Just like before, we need to set `StreamLocalBindUnlink yes` in `/etc/ssh/sshd_config`. If this isn't in place, sshd cannot clean up the stale socket in preparation for forwarding on the new one.

With all that in place, you can now try `gpg-connect-agent` and maybe even `gpg --list-secret-keys`. See if your key turns up! If it doesn't, something has gone wrong somewhere, so check out the troubleshooting section below.

### Troubleshooting - when it just doesn't work
GnuPG agent forwarding is complicated, and there's a lot of moving pieces. If just one thing is missing or there's a subtle typo, the whole thing can collapse.

The best approach is to look at things logically, start at your local machine, and work through the chain to your Ansible host.

#### Your local machine
First big question - **is the GPG agent running on your local machine?** Try `gpg-connect-agent`. Does it connect immediately, or does it suggest the agent wasn't running or is encountering an error?

#### The bastion host
Then move on and check the bastion host. Open up an SSH connection and pay careful attention. Do you see a warning that the forwarding failed? It's quite likely that your `StreamLocalBindUnlink` setting isn't working, if so. Check this, try removing the socket, closing the SSH connection, and try again.

If you can't spot an error, Try `gpg-connect-agent -S /home/XXXXX/.gnupg/S.gpg-agent-local` (or whatever path you selected for the bastion host). Does this throw an error? The most likely cause is that there's a mistake in your SSH client configuration on your local machine. Maybe the `Host` block isn't matching? Have you typo'd the path to the extra socket?

Check all of this - once you can talk to the agent from the bastion, move on.

#### The Ansible control node
The process for checking this is much the same as the bastion host. Check for warnings when opening the SSH connection, and that your client/sshd configs are correct. Verify that you can communicate with the agent with `gpg-connect-agent`.

