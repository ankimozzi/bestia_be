import { useState, useCallback, useEffect } from 'react';
import { usePlaidLink } from 'react-plaid-link';
import PropTypes from 'prop-types';

function PlaidLink({ onSuccess: parentOnSuccess }) {
  const [linkToken, setLinkToken] = useState(null);

  // Link 토큰 생성 요청
  useEffect(() => {
    const generateToken = async () => {
      try {
        const response = await fetch('http://localhost:8000/api/create_link_token', {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' }
        });
        
        if (!response.ok) {
          const errorData = await response.text();
          throw new Error(`Link token creation failed: ${errorData}`);
        }
        
        const data = await response.json();
        console.log('Link token created:', data);
        setLinkToken(data.link_token);
      } catch (error) {
        console.error('Error generating link token:', error);
      }
    };

    generateToken();
  }, []);

  // public_token을 access_token으로 교환
  const exchangePublicToken = useCallback(async (public_token) => {
    try {
      console.log('Exchanging public token:', public_token);
      const response = await fetch('http://localhost:8000/api/exchange_token', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ public_token })
      });
      
      if (!response.ok) {
        throw new Error('Token exchange failed');
      }
      
      const data = await response.json();
      console.log('Exchange token response:', data);
      
      // 기본값 설정
      return {
        ...data,
        income: data.income || 120000,
        debt: data.debt || 15000,
        credit_score: data.credit_score || 720
      };
    } catch (error) {
      console.error('Error exchanging public token:', error);
      // 에러 발생 시 기본값 반환
      return {
        income: 120000,
        debt: 15000,
        credit_score: 720
      };
    }
  }, []);

  // Plaid Link 성공 핸들러
  const onSuccess = useCallback(async (public_token, metadata) => {
    try {
      const data = await exchangePublicToken(public_token);
      console.log('Plaid success data:', data);
      parentOnSuccess({
        ...data,
        income: data.income,
        debt: data.debt,
        credit_score: data.credit_score
      });
    } catch (error) {
      console.error('Plaid Link error:', error);
      // 에러 발생 시 기본값으로 콜백 호출
      parentOnSuccess({
        income: 120000,
        debt: 15000,
        credit_score: 720
      });
    }
  }, [exchangePublicToken, parentOnSuccess]);

  const config = {
    token: linkToken,
    onSuccess,
  };

  const { open, ready } = usePlaidLink(config);

  return (
    <button 
      onClick={() => open()} 
      disabled={!ready}
      className="plaid-button"
    >
      {!ready ? 'Preparing...' : 'Connect Bank Account'}
    </button>
  );
}

PlaidLink.propTypes = {
  onSuccess: PropTypes.func.isRequired
};

export default PlaidLink;