# Debugging

## Operational Checks

```bash
scripts/02_trigger_run.sh pods
scripts/02_trigger_run.sh logs
```

## Spark Pod Inspection

```bash
kubectl -n ai-core-pipeline logs <spark-pod-name>
kubectl -n ai-core-pipeline describe pod <spark-pod-name>
```
