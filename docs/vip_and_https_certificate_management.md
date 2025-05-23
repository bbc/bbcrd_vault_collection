VIP and HTTPS certificate management
====================================

In a typical deployment you will use a Virtual IP to route all incoming
requests to a live cluster member (preferably the leader to reduce latency).

You may also wish to place Vault behind a reverse proxy to provide more
sophisticated rate limiting or abuse protection.

You will also need to handle provisioning (and renewal) of HTTPS certificates
used by Vault's public HTTPS endpoint. (This is not handled by this
collection.)

Since appropriate solutions to the above requirements can vary greatly between
deployments this collection does not attempt to tackle them. However, a
possible architecture is suggested below.


> [!NOTE]
>
> **On using non-public CAs**
>
> You may choose to use a non-public certificate authority to sign the TLS
> certificate used the Vault API. In this case, you must either ensure that
> this certificate is installed into your system's trust store or use the
> `bbcrd_vault_ca_path` variable to explicitly specify the CA root(s) to trust.
>
> Relying on the system trust store is convenient since it makes rotating
> certificates a standardised process independent of your Vault configuration.
> However, explicitly configuring Vault to trust only your certificates adds a
> layer of protection against MITM attacks involving impropperly issued public
> certificates.


Example architecture based on `ansible-keepalived` and `openstack-ansible-haproxy_server`
-----------------------------------------------------------------------------------------

As an example of one possible architecture, we can use:

* [keepalived](https://keepalived.org/) to manage a Virtual IP
* [haproxy](https://www.haproxy.org/) to act as a reverse proxy handling rate
  limiting, abuse protection and HTTPS termination
* [certbot](https://certbot.eff.org/) to handle HTTPS certificate renewal

These services can be deployed using a combination of the
[`ansible-keepalived`](https://github.com/evrardjp/ansible-keepalived) and
[`openstack-ansible-haproxy_server`](https://opendev.org/openstack/openstack-ansible-haproxy_server)
Ansible roles.

A sample set of variables for configuring this setup is shown below:


    # These need to be set per-host (rather than as group vars)
    vip_interface_name: eth0
    
    # The public hostname of this host
    host_domain: "vault-0.example.com"
    host_ip: "192.168.0.100"
    
    # The rest of these variables can be set as group vars for the whole
    # cluster
    
    # The VIP used by the cluster
    vip_ip: "192.168.0.200"
    vip_ip_cidr: "{{ vip_ip }}/24"
    vip_domain: "vault.example.com"
    
    
    # ------------------------------------------------------------------------------
    # ansible-keepalived role options
    #
    # Keepalived manages the virtual IP to keep it pointing at the leader node.
    # ------------------------------------------------------------------------------
    
    keepalived_instances:
      vault:
        interface: "{{ vip_interface_name }}"
        # start as master always, otherwise if only backups exists when we
        # start/restart then it will never take the IP and certbot will never
        # be able to obtain a certificate for the VIP domain.
        state: "MASTER"
        virtual_router_id: "{{ vip_ip.rsplit('.')[-1] | int }}"  # Must be unique on the subnet. E.g. use last octet of vip address
        track_scripts:
          # By setting a priority, we ensure keepalived will take a VIP
          # even before vault is installed.
          - "vault_check_script weight 100"
        priority: "50"
        vips:
          - "{{ vip_ip_cidr }} dev {{ vip_interface_name }}"
    
    keepalived_scripts:
      vault_check_script:
        # The Vault sys/health endpoint only returns a 200 response for
        # unsealed leader nodes, making the VIP preferentially land on the
        # leader. More importantly, it also causes the VIP to drop off any node
        # reporting as sealed as this node will also be unable to forward
        # requests to the leader.
        #
        # (429 is returned for non-leaders and 503 for sealed nodes)
        check_script: >-
          /usr/bin/curl
          --fail
          {% if bbcrd_vault_ca_path is defined %}
          --cacert {{ bbcrd_vault_ca_path }}
          {% endif %}
          {{ bbcrd_vault_public_url }}/v1/sys/health
        interval: 5    # time in seconds between each check
        fall: 2        # switch to backup after 2 failed checks
        rise: 2        # switch back to master after 2 successful checks
        timeout: 4     # allow up to 4 seconds for a check
    
    keepalived_bind_on_non_local: true  # allow services to bind to vip even when vip is not on this machine
    
    keepalived_global_defs:
      - enable_script_security
      - script_user root
    
    # ------------------------------------------------------------------------------
    # openstack-ansible-haproxy_server role options
    #
    # haproxy performs following tasks:
    #
    # * Provides HTTPS termination for the Vault API -- but *not* load balancing.
    #   Haproxy only ever forwards vault requests to the vault instance running on
    #   the same host (Vault is configured below to only listen on loopback).
    #   Vault itself will take care of forwarding requests between nodes
    #   internaly as required.
    #
    # * Optionally set up rate limits and other restrictions for the Vault API
    #   (not shown in this example)
    #
    # * Provides load balancing (i.e. simple forwarding) for the certbot HTTP
    #   server used for ACME challenges. This allows requests sent to the VIP to
    #   eventually end up on the right server which is currently engaged in a
    #   certificate renewal.
    # ------------------------------------------------------------------------------
    
    haproxy_package_state: "present"
    
    # Haproxy liveness testing
    haproxy_rise: 2
    haproxy_fall: 2
    haproxy_interval: 2000  # ms
    
    # VIP
    # The following pair of apparently non-role-related variables are
    # actually used within the implementation and also set the following
    # variables internally:
    #   * haproxy_bind_external_lb_vip_address
    #   * haproxy_bind_internal_lb_vip_address
    internal_lb_vip_address: "{{ vip_ip }}"
    external_lb_vip_address: "{{ vip_ip }}"
    
    # Another non-role-prefixed variable. Adds other IP addresses to certificates
    # which aren't the VIP.
    extra_lb_tls_vip_addresses:
      - "{{ host_ip }}"   # Set according to each host's configuration!
      - "127.0.0.1"
    
    haproxy_bind_on_non_local: true
    
    haproxy_ssl: true
    haproxy_ssl_letsencrypt_enable: True
    haproxy_ssl_letsencrypt_certbot_server: "https://ca0.{{ domain }}/acme/acme-rd/directory"
    haproxy_ssl_letsencrypt_certbot_backend_port: 80  # Required by ACME protocol
    haproxy_ssl_letsencrypt_certbot_bind_address: "{{ host_ip }}"
    haproxy_ssl_letsencrypt_email: "mist-list@rd.bbc.co.uk"
    haproxy_ssl_letsencrypt_pre_hook_timeout: 10  # seconds
    haproxy_ssl_letsencrypt_domains:
      - "{{ ansible_host }}"
      - "{{ vip_domain }}"  # VIP
    haproxy_pki_setup_host: "{{ ansible_host }}"  # Generate temporary keys on remote hosts
    
    # hatop
    haproxy_hatop_install: true
    #haproxy_hatop_download_url: "https://github.com/jhunt/hatop/archive/refs/tags/v0.8.2.tar.gz"
    haproxy_hatop_download_url: "http://mirror.{{ domain }}/hatop-0.8.2.tar.gz"
    haproxy_hatop_download_checksum: "sha256:7fac1f593f92b939cfce34175b593e43862eee8e25db251d03a910b37721fc5d"
    haproxy_hatop_download_validate_certs: true
    
    haproxy_service_configs:
      # Service for vault. Note that we use haproxy *only* for TLS termination and
      # not for HA: vault does that itself. We only route to the local Vault
      # instance (we can't reach the others over the network because Vault only
      # listens on loopback).
      - haproxy_service_name: vault
        haproxy_backend_nodes:
          - name: "{{ inventory_hostname }}"
            ip_addr: "127.0.0.1"
        haproxy_backend_port: "{{ bbcrd_vault_listen_port }}"
        haproxy_bind:
           - "{{ host_ip }}"
           - "{{ vip_ip }}"
           - "127.0.0.1"
        haproxy_port: 8200
        haproxy_balance_type: http
        haproxy_ssl: true
        haproxy_ssl_all_vips: true
      
      # Service for letsencrypt renewal via VIP (forwards to whichever host is
      # currently running the little web server)
      - haproxy_service_name: letsencrypt
        haproxy_backend_nodes: |-
          {{
            groups[bbcrd_vault_cluster_ansible_group_name]
            | zip(
              groups[bbcrd_vault_cluster_ansible_group_name]
              | map("extract", hostvars)
              | map(attribute="host_ip")
            )
            | community.general.dict
            | dict2items(key_name="name", value_name="ip_addr")
          }}
        backend_rise: 1
        backend_fall: 3
        interval: "{{ haproxy_ssl_letsencrypt_pre_hook_timeout * 1000 // 4 }}"
        haproxy_port: "{{ haproxy_ssl_letsencrypt_certbot_backend_port }}"
        haproxy_bind:  # Only bind to VIP (local IP bound by letsencrypt server)
          - "{{ vip_ip }}"
        haproxy_balance_type: http
        haproxy_backend_httpcheck_options:
          - "send meth GET uri /.well-known/ ver HTTP/1.0 hdr User-agent haproxy-healthcheck"
          - expect ! rstatus 302
    
    
    # ------------------------------------------------------------------------------
    # bbcrd.vault.*
    #
    # The options shown below will configure Vault to listen only on loopback
    # (trusting haproxy to HTTPS termination).
    # ------------------------------------------------------------------------------
    
    # The version of Vault to install
    bbcrd_vault_version: "1.17.1"
    
    # The public hostname of this host (on the other side of the haproxy HTTPS
    # termination).
    bbcrd_vault_public_url: "https://{{ host_domain }}:8200"
    
    # Listen on local network for clustering traffic
    bbcrd_vault_clustering_address: "{{ host_ip }}"
    bbcrd_vault_clustering_url: "https://{{ host_ip }}:8201"
    
    # Access via haproxy TLS termination (only listen on loopback)
    bbcrd_vault_listen_protocol: http
    bbcrd_vault_listen_address: "127.0.0.1"
    bbcrd_vault_listen_port: 8299
    bbcrd_vault_ca_path: "/usr/local/share/ca-certificates/bbcrd-lt.crt"
    
    # Trust requests from haproxy
    bbcrd_vault_x_forwarded_for_authorized_addrs:
      - "127.0.0.0/8"
