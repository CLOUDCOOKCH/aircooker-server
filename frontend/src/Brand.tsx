import { Hand } from 'lucide-react';
import { translate } from './i18n';
import type { Language } from './i18n';

/** An optional, silent fruit slap. The supplied artwork itself is never changed. */
export function Peach({ language, hero = false }: { language: Language; hero?: boolean }) {
  return (
    <button
      type="button"
      className={'peach-button' + (hero ? ' peach-button--hero' : '')}
      lang={language}
      data-peach=""
      data-peach-language={language}
      aria-label={translate(language, 'peachSlap')}
      title={translate(language, 'peachSlap')}
    >
      <img
        className={hero ? 'welcome-icon' : 'brand-peach'}
        src="/app/brand/peach-v1.png"
        alt=""
        width="384"
        height="384"
        draggable={false}
      />
      <Hand className="peach-hand" aria-hidden="true" />
    </button>
  );
}

/** Keep the peach button beside the wordmark link, never inside another control. */
export function Brand({
  compact = false,
  icon = true,
  language = 'en',
  href,
}: {
  compact?: boolean;
  icon?: boolean;
  language?: Language;
  href?: string;
}) {
  const wordmark = (
    <img
      className="brand-wordmark"
      src="/app/brand/wordmark-v1.png"
      alt="mealf"
      width="512"
      height="209"
    />
  );
  return (
    <span
      className={
        'brand-lockup' + (compact ? ' brand-lockup--compact' : '') + (href ? ' wordmark' : '')
      }
    >
      {icon && <Peach language={language} />}
      {href ? <a href={href}>{wordmark}</a> : wordmark}
    </span>
  );
}
