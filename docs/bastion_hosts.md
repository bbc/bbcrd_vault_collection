Dealing with bastion hosts/jumpboxes
====================================

In some scenarios you may not be able to access your Vault hosts directly from
the machine you are plugging your YubiKey into. One of the most likely reasons
for this is because you need to hop through a bastion host (a.k.a. a jumpbox).
There are two ways to handle this situation.

1. Run Ansible on your local machine (i.e. where the YubiKey is connected) and
   configure SSH forwarding to allow it to connect to your remote machines.

2. Use GPG agent forwarding to allow Ansible running on a remote machine to use
   your YubiKey.

The first option is easier to set up and lets the collection handle all
GPG-related details for you. The second option is necessary only if your
environment requires the use of a single, shared Ansible deployment environment
(e.g. OpenStack Ansible).


Method 1: SSH forwarding (preferred)
------------------------------------

When running Ansible on your local machine you need to configure SSH to connect
to all remote hosts via the relevant bastions/jump boxes. This can be done in
either your Ansible or SSH configurations.

To configure SSH forwarding from your Ansible inventory, set the following for
your hosts:

    ansible_ssh_common_args: '-J my-basiton.example.com'

To configure SSH forwarding from your `~/.ssh/config`:

    Match final host *.my-project.example.com
        ProxyJump my-bastion.example.com

You should then be able to run `ansible-playbook` as normal, and be able to
communicate with your Vault nodes.


Method 2 - GnuPG agent forwarding
---------------------------------

If, for whatever reason, you must run Ansible on a remote host, you can enable
GnuPG running on the remote host to use your YubiKey by forwarding a connection
from a GnuPG agent running on your local machine.

> [!WARNING]
> This approach is much more complex and also precludes the use of this
> collection's [automatic GnuPG environment
> management](../roles/ephemeral_gnupg_home).

> [!TIP]
> On MacOS, GnuPG doesn't usually come with a graphical PIN entry tool which
> will be necessary when using GnuPG agent forwarding. You can download one
> using:
>
>     $ brew install gpg pinentry-mac
>
> And configure GnuPG to use it by putting the following line into
> `/usr/local/etc/gnupg/gpg-agent.conf` (creating it if necessary):
>
>     pinentry-program /usr/local/bin/pinentry-mac

To allow the remote host to use your local GnuPG agent, we must forward the
UNIX domain socket of our local `gpg-agent` into the expected location on the
remote host using SSH's `RemoteForward` option.

**Steps:**

0. It is convenient to add the following option to `/etc/ssh/sshd_config` on
   the remote host (and then restart the SSH server):

       StreamLocalBindUnlink yes
   
   This is necessary to allow SSH to replace any existing (stale) sockets on
   the remote host with our new one when connecting.

1. Discover the location of your local gpg-agent's socket:

       $ gpgconf --list-dir agent-extra-socket
       /Users/XXXXX/.gnupg/S.gpg-agent.extra
   
   > [!INFO]
   > The 'extra' socket is a special additional socket opened by `gpg-agent`
   > which exposes a slightly more restricted set of functions than the regular
   > socket intended for forwarding.

2. Discover the expected SSH agent socket location on the remote host.

       $ ssh my-remote-host
       my-remote-host$ gpgconf --list-dir agent-socket
       /run/user/XXXXX/gnupg/S.gpg-agent

3. Make sure no `gpg-agent` is already running on the remote host:

       my-remote-host$ killall gpg-agent

4. Connect to the remote host, forwarding your GnuPG agent socket like so:

       $ ssh -o "RemoteForward <REMOTE SOCKET PATH> <LOCAL SOCKET PATH>" my-remote-host

   Using the example outputs above, that would mean:

       $ ssh -o "RemoteForward /run/user/XXXXX/gnupg/S.gpg-agent /Users/XXXXX/.gnupg/S.gpg-agent.extra" my-remote-host

   > [!IMPORTANT]
   > The paths used by GnuPG vary depending on the system and user accounts in
   > use.
   
   Alternativley, you can add add this option to your `~/.ssh/config` to make
   it the default:
   
       Host my-remote-host
           RemoteForward <REMOTE SOCKET PATH> <LOCAL SOCKET PATH>


### Verifying GnuPG agent forwarding is working

**Steps:**

0. Import your public key into the GnuPG home on the remote host:

       my-remote-host$ gpg --import /path/to/my_public_key.gpg

1. Verify that your private key is listed as available for use:
   
       my-remote-host$ gpg --list-secret-keys
       /home/example/.gnupg/pubring.kbx
       ------------------------
       sec>  rsa4096 2000-01-01 [SC]
             XXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXXX
             Card serial no. = 0000 00000000
       uid           [ unknown] John Doe (card serial 00000000) <john@example.com>
       ssb>  rsa4096 2000-01-01 [A]
       ssb>  rsa4096 2000-01-01 [E]
   
   > [!IMPORTANT]
   > SSH agent forwarding only provides remote access to secret keys, it
   > doesn't make your local GnuPG environment available from the remote host.
   > This is why it is necessary to import your public key into the remote
   > host's GnuPG home.

2. Verify PIN entry and decryption are working correctly by encrypting and
   decrypting some dummy data:

       my-remote-host$ echo "Hello world" | gpg --encrypt --recipient john@example.com -o /tmp/encrypted.gpg
       my-remote-host$ gpg --decrypt /tmp/encrypted.gpg
       gpg: encrypted with 4096-bit RSA key, ID XXXXXXXXXXXXXXXX, created 2000-01-01
             "John Doe (card serial 00000000) <john@example.com>"
       Hello world


### Troubleshooting suggestions

* Make sure `gpg-agent` is running on your local system. The following command
  should should exit successfully without any errors:

     $ echo /bye | gpg-connect-agent

* Make sure GnuPG is working in your local environment and has a *graphical*
  PIN entry program set up. Use the example `gpg --encrypt`/`gpg --decrypt`
  commands above to check this.

* Make sure you have the correct socket locations (that see `gpgconf --list-dir
  agent-extra-socket` on your local machine and `gpgconf --list-dir
  agent-socket` on the remote machine).

* Make sure the forwarded gpg-agent socket is working by running the following
  on the remote machine:

      my-remote-host$ echo /bye | gpg-connect-agent -S /run/user/XXXXX/gnupg/S.gpg-agent

* Make sure SSH is able to overwrite any existing sockets on the remote
  machine. Look out for the following warning indicating that it was not able
  to do so:

      Warning: remote port forwarding failed for listen path /run/user/XXXXX/gnupg/S.gpg-agent

  If this is failing, check that the `StreamLocalBindUnlink yes` server option has been configured. Make sure no `gpg-agent` instances are running on the remote host and try deleting the errant socket and reconnecting.

* Make sure you're skipping the [`bbcrd.vault.ephemeral_gnupg_home`
  role](../roles/ephemeral_gnupg_home), e.g. by using `--skip-tags
  bbcrd_vault_ephemeral_gnupg_home` with the provided playbooks. This will
  prevent the collection spawning its own ephemeral GnuPG environent.

* Make sure your remote GnuPG environment has your public key installed,
  without it, it won't be able to find the private key on your YubiKey.
