import { readFile } from 'node:fs/promises'
import { fileURLToPath } from 'node:url'

export const name = 'stca'
export const inject = ['skills']

// Only the package-owned skill is exposed. No provider package has to resolve
// from an unpacked folder that pnpm may install using a link: dependency.
const skillDirectory = fileURLToPath(new URL('../skills/stca', import.meta.url))
const instructionFile = fileURLToPath(new URL('../skills/stca/SKILL.md', import.meta.url))

async function definition(options = {}) {
  options.signal?.throwIfAborted()
  const raw = await readFile(instructionFile, { encoding: 'utf8', signal: options.signal })
  const parts = /^---\r?\n([\s\S]*?)\r?\n---(?:\r?\n|$)([\s\S]*)$/.exec(raw)
  if (!parts) throw new Error('STCA package is missing its instruction frontmatter.')
  const header = parts[1]
  const declaredName = /^name:\s*(?:"stca"|'stca'|stca)\s*$/m.test(header)
  // This repository emits its description as a JSON-quoted YAML scalar.
  const quotedDescription = /^description:\s*("[^\r\n]*")\s*$/m.exec(header)?.[1]
  if (!declaredName || !quotedDescription) throw new Error('STCA package metadata is incomplete.')
  const description = JSON.parse(quotedDescription)
  if (typeof description !== 'string' || !description.trim()) throw new Error('STCA package description is empty.')
  const boolean = (key, fallback) => {
    const value = new RegExp(`^${key}:\\s*(true|false)\\s*$`, 'm').exec(header)?.[1]
    return value === undefined ? fallback : value === 'true'
  }
  return {
    name: 'stca',
    description,
    invocation: {
      modelInvocable: !boolean('disable-model-invocation', false),
      userInvocable: boolean('user-invocable', true),
    },
    source: 'bundled',
    provider: 'stca',
    path: instructionFile,
    resourceBase: { kind: 'directory', path: skillDirectory },
    content: parts[2].trim(),
  }
}

export function apply(ctx) {
  ctx.skills.registerProvider(() => ({
    name: 'stca',
    async list(options) {
      const { content, ...summary } = await definition(options)
      return [{ ...summary, rank: 600, locator: { path: instructionFile } }]
    },
    async get(candidate, options) {
      if (candidate.name !== 'stca' || candidate.provider !== 'stca') return undefined
      return definition(options)
    },
  }))
}
