/** Public links of the website: update at publication time (GitHub repository, technical note, contact). */
export const LINKS = {
  site: 'https://wapp-dam-simulator.mastereose.fr',
  github: 'https://github.com/aymardino/wapp-dam-simulator',
  issues: 'https://github.com/aymardino/wapp-dam-simulator/issues',
  rules: 'https://github.com/aymardino/wapp-dam-simulator/blob/main/docs/MARKET_RULES.md',
  data: 'https://github.com/aymardino/wapp-dam-simulator/blob/main/docs/REFERENCE_DATA.md',
  architecture: 'https://github.com/aymardino/wapp-dam-simulator/blob/main/docs/ARCHITECTURE.md',
  deploy: 'https://github.com/aymardino/wapp-dam-simulator/blob/main/docs/DEPLOYMENT.md',
  sheet: 'https://github.com/aymardino/wapp-dam-simulator/blob/main/docs/TECHNICAL_SHEET.md',
  sheet_fr: 'https://github.com/aymardino/wapp-dam-simulator/blob/main/docs/fr/FICHE_TECHNIQUE.md',
  licence: 'https://www.apache.org/licenses/LICENSE-2.0',
  paper: null as string | null,
  // Explanatory video: a YouTube / Vimeo embed URL, the path of an .mp4 file, or one file per language with its
  // poster. The section appears when set. The files below are rendered from video/ (HyperFrames, npm run render).
  video: {
    fr: { src: '/video/wapp-dam-simulator-fr.mp4', poster: '/video/poster-fr.jpg' },
    en: { src: '/video/wapp-dam-simulator-en.mp4', poster: '/video/poster-en.jpg' },
  } as string | Record<'fr' | 'en', { src: string; poster?: string }> | null,
  // Contact e-mail shown in the About section, as [local part, domain]: the full address is only assembled in the
  // browser, so that it does not appear as plain text in the published files (fewer spam harvesters). null hides it.
  contact: ['kodjovi-aymard.plakoo', 'minesparis.psl.eu'] as [string, string] | null,   // note technique / working paper : renseigner l'URL quand elle est publiée
}
