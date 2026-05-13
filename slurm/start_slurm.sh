nodes=(vm1 vm2 vm3)
ssh vm0 sudo systemctl enable --now slurmctld
ssh vm0 sudo systemctl start --now slurmctld
for node in ${nodes[@]};
do echo $node;
ssh $node sudo systemctl enable --now slurmd;
ssh $node sudo systemctl start slurmd;
done

