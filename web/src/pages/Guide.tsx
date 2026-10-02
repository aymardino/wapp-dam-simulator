import { useEffect, useState } from 'react'
import { useParams } from 'react-router-dom'
import { marked } from 'marked'
import { useLang, useT } from '../i18n'
import { Header } from '../components/ui'

/** Guides du formateur et du trader, servis en Markdown depuis /guides/<qui>.<langue>.md */
export default function Guide() {
  const { who = 'trader' } = useParams(); const { lang } = useLang(); const t = useT()
  const [html, setHtml] = useState('')
  useEffect(() => {
    fetch(`/guides/${who === 'formateur' ? 'formateur' : 'trader'}.${lang}.md`).then(r => r.text()).then(md => setHtml(marked.parse(md) as string)).catch(() => setHtml(''))
  }, [who, lang])
  return (
    <div className="min-h-screen">
      <Header title={who === 'formateur' ? t('guide_trainer') : t('guide_trader')} />
      <main className="max-w-3xl mx-auto px-6 py-10 guide" dangerouslySetInnerHTML={{ __html: html }} />
    </div>
  )
}
