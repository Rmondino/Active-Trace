import { useQuery } from '@tanstack/react-query'
import { useAuth } from '@/shared/hooks/useAuth'
import { comisionService } from '../services/comisionService'

export function useAsignaciones() {
  const { user } = useAuth()
  return useQuery({
    queryKey: ['asignaciones', user?.id],
    queryFn: () => comisionService.getAsignaciones(user!.id),
    enabled: !!user?.id,
  })
}
