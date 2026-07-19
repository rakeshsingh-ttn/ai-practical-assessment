export function ErrorBanner({ message, onDismiss }) {
  if (!message) return null;
  return (
    <div className="banner banner-error">
      <span>{message}</span>
      {onDismiss && (
        <button type="button" className="btn-text" onClick={onDismiss}>
          Dismiss
        </button>
      )}
    </div>
  );
}

export function FieldError({ error }) {
  if (!error) return null;
  return <p className="field-error">{error}</p>;
}

export function formatApiError(err) {
  if (!err) return 'An unexpected error occurred';
  if (err.status === 422 && Array.isArray(err.details)) {
    return err.details.map((d) => `${d.loc?.join('.')}: ${d.msg}`).join('; ');
  }
  return err.message || 'Request failed';
}
