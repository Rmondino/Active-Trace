import { useQuery } from '@tanstack/react-query'
import { monitorService } from '../services/monitorService'
import type { MonitorFilters } from '../types/monitor'

export function useMonitor(filters: MonitorFilters) {
  return useQuery({
    queryKey: ['monitor', filters],
    queryFn: () => monitorService.list(filters),
  })
}
