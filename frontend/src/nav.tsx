import { createContext, useContext } from 'react'
import type { HistoryRide, Me, MyTrip, RosterDriver, TripCard } from './api'
import type { Lang } from './strings'

export type Screen =
  | { name: 'driverHome' }
  | { name: 'postTrip' }
  | { name: 'myTrips' }
  | { name: 'requestsNear' }
  | { name: 'riderHome' }
  | { name: 'findRide'; mode: 'search' | 'request' }
  | { name: 'results'; destId: number; destNameAm: string; destNameEn: string; when: string }
  | { name: 'tripCard'; card: TripCard }
  | { name: 'myBookings' }
  | { name: 'womenOnly' }
  | { name: 'saved' }
  | { name: 'admin' }
  | { name: 'addDriver'; edit?: RosterDriver }
  | { name: 'receipt'; ride: HistoryRide }
  | { name: 'report'; trip_id: number; driver_name: string }
  | { name: 'editTrip'; trip: MyTrip }
  | { name: 'profile' }
  | { name: 'support' }
  | { name: 'broadcast' }
  | {
      name: 'ridePreview'; trip_id: number; to_place_id: number
      dest_name_am: string; dest_name_en: string
      driver_name: string; driver_tower: string | null
      car_model: string | null; car_color: string | null; plate: string | null
      depart_at: string; fare: number; seats_left?: number
    }

export interface Nav {
  me: Me
  go(s: Screen): void
  back(): void
  reset(s: Screen): void
  isAdmin: boolean
  lang: Lang
  toggleLang(): void
}

export const NavCtx = createContext<Nav>(null as unknown as Nav)
export const useNav = () => useContext(NavCtx)
