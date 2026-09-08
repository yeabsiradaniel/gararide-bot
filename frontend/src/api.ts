// Typed API client. Sends Authorization: tma <initData> on every request.
import { initData } from './telegram'

const BASE = (import.meta.env.VITE_API_BASE as string) ?? ''

export class ApiError extends Error {
  constructor(public status: number, public detail?: string) {
    super(detail || `HTTP ${status}`)
  }
}

async function req<T>(path: string, opts: RequestInit = {}): Promise<T> {
  const res = await fetch(BASE + path, {
    ...opts,
    headers: {
      'Content-Type': 'application/json',
      Authorization: 'tma ' + initData(),
      ...(opts.headers || {}),
    },
  })
  if (res.status === 204) return null as T
  const body = await res.json().catch(() => null)
  if (!res.ok) throw new ApiError(res.status, body?.detail)
  return body as T
}

const post = <T>(path: string, data?: unknown) =>
  req<T>(path, { method: 'POST', body: data ? JSON.stringify(data) : undefined })

const del = <T>(path: string) => req<T>(path, { method: 'DELETE' })

// ---- types (mirror the backend response shapes) ----
export interface Me {
  telegram_id: number; full_name: string; role: 'driver' | 'rider'
  tower: string | null; car_model: string | null; plate: string | null
  car_seats: number | null; women_only: boolean; women_present: boolean
  is_admin: boolean; lang: 'am' | 'en'
}
export interface Place { id: number; slug: string; name_am: string; name_en: string; sort_order: number }
export interface DropoffOptions { intermediate: Place[]; destination: Place }
export interface FareLine { place_id: number; slug: string; name_am: string; fare: number }
export interface PostedTrip { trip_id: number; dest_place_id: number; depart_at: string; seats: number; fares: FareLine[] }
export interface Passenger { booking_id: number; name: string; tower: string | null; to_place_id: number; to_name_am: string; fare: number; phone: string; paid: boolean }
export interface MyTrip { trip_id: number; dest_place_id: number; dest_name_am: string; depart_at: string; seats_total: number; seats_left: number; passengers: Passenger[] }
export interface NearRequest { request_id: number; rider_name: string; dest_place_id: number; dest_name_am: string; window_start: string; window_end: string }
export interface Match { trip_id: number; driver_name: string; driver_tower: string | null; depart_at: string; seats_left: number; fare: number }
export interface NearMiss { trip_id: number; driver_name: string; depart_at: string; fare: number; dest_place_id: number; dest_name_am: string; reason: 'earlier' | 'later' | 'partway' }
export interface SearchResult { matches: Match[]; near_misses: NearMiss[]; demand_count: number }
export interface TripCard { booking_id: number; trip_id: number; depart_at: string; bay: string; driver_name: string; driver_tower: string | null; car_model: string | null; plate: string | null; phone: string; dest_place_id: number; dest_name_am: string; fare: number }
export interface SavedTrip { id: number; dest_place_id: number; dest_name_am: string; depart_time: string; days_mask: number }
export interface DriverRoute { id: number; dest_place_id: number; dest_name_am: string; depart_time: string; seats: number; days_mask: number }
export interface PostedRoute { trip_id: number; already: boolean; depart_at: string; seats: number; dest_name_am: string; fares: FareLine[] }
export interface Ops { trips: number; seats: number; no_shows: number; open_requests: number; users: number }
export interface Unmatched { dest_name: string; riders: number }
export interface RosterDriver {
  phone: string; full_name: string; tower: string; role: string
  car_model: string | null; plate: string | null; car_seats: number | null
  is_female: boolean; onboarded: boolean
}
export interface NewDriver {
  phone: string; full_name: string; tower: string
  car_model?: string | null; plate?: string | null; car_seats: number; is_female?: boolean
}

export const api = {
  me: () => req<Me>('/me'),
  setLang: (lang: 'am' | 'en') => post<null>('/me/lang', { lang }),
  places: () => req<Place[]>('/places'),
  // driver
  dropoffOptions: (destId: number) => req<DropoffOptions>(`/trips/${destId}/dropoff-options`),
  postTrip: (b: { dest_place_id: number; dropoff_place_ids: number[]; depart_at: string; seats: number; note?: string | null }) =>
    post<PostedTrip>('/trips', b),
  myTrips: () => req<MyTrip[]>('/trips/mine'),
  cancelTrip: (id: number) => post<null>(`/trips/${id}/cancel`),
  // driver saved routes (one-tap repeat)
  routes: () => req<DriverRoute[]>('/routes'),
  saveRoute: (b: { dest_place_id: number; dropoff_place_ids: number[]; depart_time: string; seats: number; days_mask: number }) =>
    post<DriverRoute>('/routes', b),
  deleteRoute: (id: number) => del<null>(`/routes/${id}`),
  postRoute: (id: number) => post<PostedRoute>(`/routes/${id}/post`),
  requestsNear: () => req<NearRequest[]>('/requests/near'),
  markPaid: (id: number) => post<null>(`/bookings/${id}/paid`),
  markNoShow: (id: number) => post<null>(`/bookings/${id}/no-show`),
  // rider
  search: (destId: number, when: string) =>
    req<SearchResult>(`/trips/search?dest_place_id=${destId}&when=${when}`),
  book: (trip_id: number, to_place_id: number) => post<TripCard>('/bookings', { trip_id, to_place_id }),
  cancelBooking: (id: number) => post<null>(`/bookings/${id}/cancel`),
  myBookings: () => req<TripCard[]>('/bookings/mine'),
  postRequest: (dest_place_id: number, window_start: string, window_end: string) =>
    post<{ request_id: number }>('/requests', { dest_place_id, window_start, window_end }),
  block: (trip_id: number) => post<null>('/blocks', { trip_id }),
  setWomenOnly: (women_only: boolean, women_present: boolean) =>
    post<null>('/me/women-only', { women_only, women_present }),
  // saved
  saved: () => req<SavedTrip[]>('/me/saved'),
  addSaved: (dest_place_id: number, depart_time: string, days_mask: number) =>
    post<{ id: number }>('/me/saved', { dest_place_id, depart_time, days_mask }),
  deactivateSaved: (id: number) => post<null>(`/me/saved/${id}/deactivate`),
  // admin
  ops: () => req<Ops>('/admin/ops'),
  unmatched: () => req<Unmatched[]>('/admin/unmatched'),
  drivers: () => req<RosterDriver[]>('/admin/drivers'),
  addDriver: (b: NewDriver) => post<RosterDriver>('/admin/drivers', b),
  removeDriver: (phone: string) =>
    del<{ removed: string; was_onboarded: boolean; trips_cancelled: number }>(
      '/admin/drivers/' + encodeURIComponent(phone)),
}
