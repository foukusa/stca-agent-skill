import { fileURLToPath } from 'node:url'
import { apply as mountSkills } from '@deepseek-ai/dsh-skill-filesystem'

export const name = 'stca'
export const inject = ['skills']

export function apply(ctx) {
  mountSkills(ctx, {
    providerName: 'stca',
    includeDefaultRoots: false,
    bundledSkillDir: fileURLToPath(new URL('../skills/', import.meta.url)),
    watch: false,
  })
}
