import { readFile } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'
import { BUNDLED_SKILL_RANK } from '@deepseek-ai/dsh-skill'

const PROVIDER_NAME = 'project-orrery'
const SKILL_URL = new URL('./SKILL.md', import.meta.url)
const RESOURCE_BASE = {
  kind: 'directory',
  path: fileURLToPath(new URL('./', import.meta.url)),
}
const INVOCATION = { modelInvocable: true, userInvocable: true }
const DESCRIPTION = 'Route Orrery documentation-system work through the platform-neutral Orrery CLI while preserving the target repository canonical AGENTS.md authority chain. Use when asked to scaffold, validate, audit, update, or maintain Orrery documentation.'
const CANDIDATE = {
  name: 'project-orrery',
  description: DESCRIPTION,
  invocation: INVOCATION,
  provider: PROVIDER_NAME,
  source: 'bundled',
  resourceBase: RESOURCE_BASE,
  rank: BUNDLED_SKILL_RANK,
  locator: SKILL_URL,
}

const provider = {
  name: PROVIDER_NAME,
  list: () => Promise.resolve([CANDIDATE]),
  async get() {
    return {
      name: CANDIDATE.name,
      description: CANDIDATE.description,
      invocation: CANDIDATE.invocation,
      provider: CANDIDATE.provider,
      source: CANDIDATE.source,
      resourceBase: RESOURCE_BASE,
      content: await readFile(SKILL_URL, 'utf8'),
    }
  },
}

export const name = 'project-orrery-skill'
export const inject = ['skills']

export function apply(ctx) {
  ctx.skills.registerProvider(() => provider)
}
