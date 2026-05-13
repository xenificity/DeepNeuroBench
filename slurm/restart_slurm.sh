nodes=(vm1 vm2 vm3)
ssh vm0 sudo systemctl restart slurmctld
for node in ${nodes[@]};
do echo $node;
ssh $node sudo systemctl restart slurmd;
done
