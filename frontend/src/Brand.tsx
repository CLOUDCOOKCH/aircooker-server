/** Supplied artwork, with one accessible brand name and decorative peach. */
export function Brand({ compact = false, icon = true }: { compact?: boolean; icon?: boolean }) {
  return (
    <span className={'brand-lockup' + (compact ? ' brand-lockup--compact' : '')}>
      {icon && (
        <img
          className="brand-peach"
          src="/app/brand/peach-v1.png"
          alt=""
          width="384"
          height="384"
        />
      )}
      <img
        className="brand-wordmark"
        src="/app/brand/wordmark-v1.png"
        alt="mealf"
        width="512"
        height="209"
      />
    </span>
  );
}
