import { createContext, useContext } from 'react'
import type { Me, TripCard } from './api'

export type Screen =
  | { name: 'driverHome' }
  | { name: 'postTrip' }
  | { name: 'myTrips' }
  | { name: 'requestsNear' }
  | { name: 'riderHome' }
  | { name: 'findRide'; mode: 'search' | 'request' }
  | { name: 'results'; destId: number; destName: string; when: string }
  | { name: 'tripCard'; card: TripCard }
  | { name: 'myBookings' }
  | { name: 'womenOnly' }
  | { name: 'saved' }
  | { name: 'admin' }
  | { name: 'addDriver' }

export interface Nav {
  me: Me
  go(s: Screen): void
  back(): void
  reset(s: Screen): void
  isAdmin: boolean
}

export const NavCtx = createContext<Nav>(null as unknown as Nav)
export const useNav = () => useContext(NavCtx)
