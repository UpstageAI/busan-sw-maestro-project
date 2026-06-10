import { useState, useRef } from 'react';

function EmailModal({ isOpen, onClose, curriculumMarkdown, onSendEmail }) {
  const [email, setEmail] = useState('');
  const [sending, setSending] = useState(false);
  const [success, setSuccess] = useState(false);
  const [error, setError] = useState('');
  const overlayRef = useRef(null);

  const handleOverlayClick = (e) => {
    if (e.target === overlayRef.current) onClose();
  };

  const handleSubmit = async () => {
    if (!email || !email.includes('@')) {
      alert('유효한 이메일 주소를 입력해주세요.');
      return;
    }

    setSending(true);
    setError('');

    try {
      await onSendEmail({ email, markdown: curriculumMarkdown });
      setSuccess(true);
      setTimeout(() => {
        onClose();
        setSuccess(false);
        setEmail('');
      }, 3000);
    } catch (err) {
      setError('이메일 전송에 실패했습니다. 다시 시도해주세요.');
      console.error('이메일 전송 실패:', err);
    } finally {
      setSending(false);
    }
  };

  const handleClose = () => {
    onClose();
    setSuccess(false);
    setEmail('');
    setSending(false);
    setError('');
  };

  return (
    <div
      ref={overlayRef}
      className={`mp-modal-overlay${isOpen ? ' active' : ''}`}
      onClick={handleOverlayClick}
    >
      <div className="mp-modal-box" onClick={(e) => e.stopPropagation()}>
        <p className="mp-modal-title">{success ? 'SUCCESS' : 'SEND TO EMAIL'}</p>

        {/* Form */}
        {!success && (
          <div className="mp-modal-form" style={{ opacity: sending ? 0.5 : 1 }}>
            <input
              className="mp-modal-input"
              placeholder="Enter your email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={sending}
            />
            {error && (
              <p style={{ color: '#f87171', fontSize: '13px', margin: '4px 0 0' }}>
                {error}
              </p>
            )}
            <button
              className="mp-modal-submit"
              onClick={handleSubmit}
              disabled={sending}
            >
              {sending ? '전송 중...' : 'SUBMIT'}
            </button>
          </div>
        )}

        {/* Success */}
        <div className={`mp-success-msg${success ? ' active' : ''}`}>
          <span className="material-symbols-outlined mp-success-icon">check_circle</span>
          <div>
            <p className="mp-success-text">이메일을 전송하였습니다!</p>
            <p className="mp-success-sub">입력하신 주소로 커리큘럼이 발송되었습니다.</p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default EmailModal;
