nodes=(vm1 vm2 vm3)
ssh vm0 sudo systemctl status slurmctld
for node in ${nodes[@]};
do echo $node;
ssh $node sudo systemctl status slurmd;
done

