import { auth, currentUser } from '@clerk/nextjs/server'

export async function getOrgId(): Promise<string> {
  const { orgId } = await auth()
  if (!orgId) throw new Error('No org selected')
  return orgId
}

export async function getRole(): Promise<string> {
  const { orgRole } = await auth()
  return orgRole ?? 'member'
}

export async function requireAuth() {
  const { userId } = await auth()
  if (!userId) throw new Error('Unauthenticated')
  return userId
}
