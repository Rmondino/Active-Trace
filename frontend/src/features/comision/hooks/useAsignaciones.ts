import { useQuery } from '@tanstack/react-query'
import { comisionService } from '../services/comisionService'

export function useAsignaciones() {
  return useQuery({
    queryKey: ['asignaciones'],
    queryFn: () => comisionService.getAsignaciones(),
  })
}
