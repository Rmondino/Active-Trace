import { useState, useEffect } from 'react'
import { usePerfil, useActualizarPerfil } from '@/features/perfil/hooks/usePerfil'
import { LoadingSpinner } from '@/shared/components/LoadingSpinner'
import { ErrorMessage } from '@/shared/components/ErrorMessage'

export function PerfilPage() {
  const { data: perfil, isLoading, isError, error } = usePerfil()
  const mutation = useActualizarPerfil()

  const [nombre, setNombre] = useState('')
  const [apellidos, setApellidos] = useState('')
  const [cbu, setCbu] = useState('')
  const [aliasCbu, setAliasCbu] = useState('')
  const [banco, setBanco] = useState('')
  const [regional, setRegional] = useState('')
  const [successMsg, setSuccessMsg] = useState('')

  useEffect(() => {
    if (perfil) {
      setNombre(perfil.nombre ?? '')
      setApellidos(perfil.apellidos ?? '')
      setCbu(perfil.cbu ?? '')
      setAliasCbu(perfil.alias_cbu ?? '')
      setBanco(perfil.banco ?? '')
      setRegional(perfil.regional ?? '')
    }
  }, [perfil])

  useEffect(() => {
    if (mutation.isSuccess) {
      setSuccessMsg('Perfil actualizado correctamente')
      setTimeout(() => setSuccessMsg(''), 3000)
    }
  }, [mutation.isSuccess])

  if (isLoading) return <LoadingSpinner size="lg" className="mt-12" />
  if (isError) return <ErrorMessage message={(error as Error)?.message ?? 'Error al cargar el perfil'} />

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    setSuccessMsg('')
    mutation.mutate({
      nombre,
      apellidos,
      cbu: cbu || null,
      alias_cbu: aliasCbu || null,
      banco: banco || null,
      regional: regional || null,
    })
  }

  const readOnlyClass = 'w-full rounded-md border border-gray-200 bg-gray-100 px-3 py-2 text-sm text-gray-600'
  const inputClass = 'w-full rounded-md border border-gray-300 px-3 py-2 text-sm focus:border-blue-500 focus:outline-none focus:ring-1 focus:ring-blue-500'

  return (
    <div className="mx-auto max-w-2xl">
      <h1 className="mb-6 text-2xl font-bold text-gray-900">Mi Perfil</h1>

      {successMsg && (
        <div className="mb-4 rounded-md bg-green-50 p-3 text-sm text-green-700" role="status">
          {successMsg}
        </div>
      )}

      {mutation.isError && (
        <div className="mb-4 rounded-md bg-red-50 p-3 text-sm text-red-700" role="alert">
          {(mutation.error as Error)?.message ?? 'Error al actualizar'}
        </div>
      )}

      <form onSubmit={handleSubmit} className="space-y-6">
        <section>
          <h2 className="mb-3 text-lg font-semibold text-gray-700">Datos personales</h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-500">Email</label>
              <input type="text" value={perfil!.email} readOnly className={readOnlyClass} />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-500">DNI</label>
              <input type="text" value={perfil!.dni} readOnly className={readOnlyClass} />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-500">CUIL</label>
              <input type="text" value={perfil!.cuil} readOnly className={readOnlyClass} />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-500">Legajo</label>
              <input type="text" value={perfil!.legajo} readOnly className={readOnlyClass} />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-500">Legajo profesional</label>
              <input type="text" value={perfil!.legajo_profesional ?? '-'} readOnly className={readOnlyClass} />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-500">Nombre</label>
              <input type="text" value={nombre} onChange={(e) => setNombre(e.target.value)} className={inputClass} />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-500">Apellidos</label>
              <input type="text" value={apellidos} onChange={(e) => setApellidos(e.target.value)} className={inputClass} />
            </div>
          </div>
        </section>

        <section>
          <h2 className="mb-3 text-lg font-semibold text-gray-700">Datos bancarios</h2>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-500">CBU</label>
              <input type="text" value={cbu} onChange={(e) => setCbu(e.target.value)} className={inputClass} />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-500">Alias CBU</label>
              <input type="text" value={aliasCbu} onChange={(e) => setAliasCbu(e.target.value)} className={inputClass} />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-500">Banco</label>
              <input type="text" value={banco} onChange={(e) => setBanco(e.target.value)} className={inputClass} />
            </div>
            <div>
              <label className="mb-1 block text-xs font-medium text-gray-500">Regional</label>
              <input type="text" value={regional} onChange={(e) => setRegional(e.target.value)} className={inputClass} />
            </div>
          </div>
        </section>

        <div className="flex justify-end">
          <button
            type="submit"
            disabled={mutation.isPending}
            className="rounded-md bg-blue-600 px-6 py-2 text-sm font-medium text-white hover:bg-blue-700 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {mutation.isPending ? 'Guardando…' : 'Guardar cambios'}
          </button>
        </div>
      </form>
    </div>
  )
}
