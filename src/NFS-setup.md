# NFS Configuration Guide

This guide provides step-by-step instructions on how to configure Network File System (NFS) on multiple virtual machines (VMs).

## Step 1: Configure NFS Server on vm1

1. **Install NFS server**: Update your package lists and install the NFS Kernel Server.

    ```bash
    sudo apt update
    sudo apt install nfs-kernel-server -y
    ```

2. **Create a shared directory**: This directory will be shared with the client VMs.

    ```bash
    sudo mkdir -p /mydata
    sudo chown -R ubuntu:ubuntu /mydata
    sudo chmod -R 777 /mydata/
    ```

3. **Configure export files**: Edit the `/etc/exports` file and add the following line:

    ```bash
    sudo vim /etc/exports
    ```

    Add the line:

    ```
    /mydata 192.168.1.1/24(rw,sync,no_subtree_check)
    ```

    > Note: `192.168.1.1` is the IP address of vm1, where the NFS server is running.

4. **Apply the changes**: Export the shared directory and restart the NFS server to apply the changes.

    ```bash
    sudo exportfs -a
    sudo systemctl restart nfs-kernel-server
    ```

## Step 2: Configure NFS Client on each VM (vm1,vm2, vm3, ... vmn)
Install NFS client, Create mount point, Mount NFS shared directory, Make mount persistent
   
```
nodes=(vm1 vm2 vm3) #please feel free to change as per your worker nodes
for node in "${nodes[@]}";do
ssh $node '
sudo apt update
sudo apt install nfs-common -y
sudo mkdir -p /mydata
sudo mount 192.168.1.1:/mydata /mydata
echo "192.168.1.1:/mydata /mydata nfs auto,nofail,noatime,nolock,intr,tcp,actimeo=1800 0 0" | sudo tee -a /etc/fstab '
done
```
    
> Note: Replace `192.168.1.1` with the IP address of your NFS server.

That's it! You have now configured NFS on your VMs.

