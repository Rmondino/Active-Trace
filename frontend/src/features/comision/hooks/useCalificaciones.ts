import { useQuery, useMutation } from '@tanstack/react-query'
import { calificacionesService } from '../services/calificacionesService'

export function useCalificaciones(materiaId: string) {
  return useQuery({
    queryKey: ['calificaciones', materiaId],
    queryFn: () => calificacionesService.list(materiaId),
  })
}

export function useUploadPreview() {
  return useMutation({
    mutationFn: ({ file, materiaId, cohorteId }: { file: File; materiaId: string; cohorteId: string }) =>
      calificacionesService.uploadPreview(file, materiaId, cohorteId),
  })
}

export function useConfirmImport() {
  return useMutation({
    mutationFn: ({ previewId, actividadesSeleccionadas }: { previewId: string; actividadesSeleccionadas: string[] | null }) =>
      calificacionesService.confirm(previewId, actividadesSeleccionadas),
  })
}

export function useUploadCompletions() {
  return useMutation({
    mutationFn: ({ file, materiaId }: { file: File; materiaId: string }) =>
      calificacionesService.uploadCompletions(file, materiaId),
  })
}
