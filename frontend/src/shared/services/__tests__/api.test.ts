import { describe, it, expect, vi, beforeEach } from 'vitest'

const mockAxiosSetup = vi.hoisted(() => {
  const mockAxiosPost = vi.fn()
  const mockInstanceRequest = vi.fn()
  const handlerCapture: { current: ((error: unknown) => unknown) | undefined } = {
    current: undefined,
  }

  const instance = vi.fn((config: unknown) => mockInstanceRequest(config))
  instance.defaults = { baseURL: 'http://localhost:8000' }
  instance.interceptors = {
    request: { use: vi.fn() },
    response: {
      use: vi.fn((_fulfilled: unknown, rejected: ((error: unknown) => unknown) | undefined) => {
        handlerCapture.current = rejected
      }),
    },
  }
  instance.get = vi.fn()
  instance.post = vi.fn()
  instance.request = vi.fn()

  return { mockAxiosPost, mockInstanceRequest, handlerCapture, instance }
})

vi.mock('axios', () => ({
  default: {
    create: vi.fn(() => mockAxiosSetup.instance),
    post: mockAxiosSetup.mockAxiosPost,
  },
  create: vi.fn(() => mockAxiosSetup.instance),
  post: mockAxiosSetup.mockAxiosPost,
}))

describe('api interceptor de refresh', () => {
  beforeEach(() => {
    localStorage.setItem('access_token', 'test-access-token')
    localStorage.setItem('refresh_token', 'test-refresh-token')
    vi.clearAllMocks()
  })

  it('reintenta la request original después de refrescar el token en un 401', async () => {
    await import('@/shared/services/api')

    const handler = mockAxiosSetup.handlerCapture.current
    expect(handler).toBeDefined()

    mockAxiosSetup.mockAxiosPost.mockResolvedValue({
      data: {
        access_token: 'new-access-token',
        refresh_token: 'new-refresh-token',
      },
    })

    mockAxiosSetup.mockInstanceRequest.mockResolvedValue({ data: 'retried' })

    const error = {
      response: { status: 401 },
      config: {
        url: '/api/protected-resource',
        headers: {},
        _retry: false,
      },
    }

    const result = await (handler as (error: unknown) => Promise<unknown>)(error)

    expect(mockAxiosSetup.mockAxiosPost).toHaveBeenCalledWith(
      'http://localhost:8000/api/auth/refresh',
      { refresh_token: 'test-refresh-token' },
    )

    expect(localStorage.getItem('access_token')).toBe('new-access-token')
    expect(localStorage.getItem('refresh_token')).toBe('new-refresh-token')

    expect(mockAxiosSetup.mockInstanceRequest).toHaveBeenCalledWith(
      expect.objectContaining({
        url: '/api/protected-resource',
        headers: expect.objectContaining({
          Authorization: 'Bearer new-access-token',
        }),
      }),
    )

    expect(result).toEqual({ data: 'retried' })
  })

  it('no intercepta requests que no son 401', async () => {
    await import('@/shared/services/api')

    const handler = mockAxiosSetup.handlerCapture.current
    expect(handler).toBeDefined()

    const error = {
      response: { status: 403 },
      config: { url: '/api/something', headers: {}, _retry: false },
    }

    await expect(
      (handler as (error: unknown) => Promise<unknown>)(error),
    ).rejects.toEqual(error)

    expect(mockAxiosSetup.mockAxiosPost).not.toHaveBeenCalled()
  })
})
