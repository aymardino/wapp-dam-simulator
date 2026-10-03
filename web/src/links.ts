/** Public links of the website: update at publication time (GitHub repository, technical note, contact). */
export const LINKS = {
  site: 'https://wapp-dam-simulator.org',
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
  video: null as string | null,   // explanatory video: a YouTube / Vimeo embed URL or the path of an .mp4 file; the section appears when set
  // Contact e-mail shown in the About section, as [local part, domain]: the full address is only assembled in the
  // browser, so that it does not appear as plain text in the published files (fewer spam harvesters). null hides it.
  contact: ['kodjovi-aymard.plakoo', 'minesparis.psl.eu'] as [string, string] | null,   // note technique / working paper : renseigner l'URL quand elle est publiée
}
