import { useState } from 'react';
import PropTypes from 'prop-types';
import PlaidLink from './PlaidLink';
import './MortgageBot.css';

function MortgageBot({ onClose, propertyPrice, propertyAddress }) {
  const [plaidData, setPlaidData] = useState(null);
  const [formData, setFormData] = useState({
    loan_amount: '',
    down_payment: propertyPrice ? Math.round(propertyPrice * 0.2) : '', // 기본 계약금 20% 설정
  });
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handlePlaidSuccess = (data) => {
    setPlaidData({
      ...data,
      annual_income: data.income || 0,
      total_debt: data.debt || 0,
      credit_score: data.credit_score || 0
    });
    setResult('✅ Account linked! Please enter loan details below.');
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!plaidData) {
      setResult('Please link your bank account first.');
      return;
    }
    
    setLoading(true);

    try {
      const mortgageData = {
        home_value: propertyPrice,
        loan_amount: Number(formData.loan_amount),
        down_payment: Number(formData.down_payment),
        annual_income: plaidData.annual_income,
        total_debt: plaidData.total_debt,
        credit_score: plaidData.credit_score
      };

      const response = await fetch('http://localhost:8000/api/mortgage-analysis/', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(mortgageData)
      });
      
      const data = await response.json();

      const message = `🏡 **Mortgage Analysis Results**:
        
        📍 Property Information
        - Address: ${propertyAddress}
        - Price: $${propertyPrice.toLocaleString()}
        
        💰 Loan Details
        - Loan Amount: $${mortgageData.loan_amount.toLocaleString()}
        - Down Payment: $${mortgageData.down_payment.toLocaleString()}
        - Monthly Payment: $${data.monthly_payment.toLocaleString()}
        
        📊 Financial Status
        - Annual Income: $${mortgageData.annual_income.toLocaleString()}
        - Current Debt: $${mortgageData.total_debt.toLocaleString()}
        - Credit Score: ${mortgageData.credit_score}
        
        📈 Loan Metrics
        - DTI Ratio: ${data.DTI_ratio}%
        - LTV Ratio: ${data.LTV_ratio}%
        
        ✨ Approval Status: ${data.approval_status === "Approved" ? "✅ Approved" : "❌ Not Approved"}
        
        Detailed Review:
        ${Object.entries(data.approval_details)
          .map(([key, value]) => `${key}: ${value}`)
          .join('\n        ')}`;

      setResult(message);
    } catch (error) {
      console.error('Error:', error);
      setResult('An error occurred during analysis.');
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: value
    }));
  };

  return (
    <div className="mortgage-bot">
      <div className="mortgage-bot-header">
        <h2>Mortgage Consultation</h2>
        <button onClick={onClose}>&times;</button>
      </div>

      <div className="property-info">
        <p>Address: {propertyAddress}</p>
        <p>Price: ${propertyPrice?.toLocaleString()}</p>
      </div>

      <div className="plaid-section">
        {!plaidData ? (
          <>
            <p>Link your bank account to get financial information</p>
            <PlaidLink onSuccess={handlePlaidSuccess} />
          </>
        ) : (
          <div className="financial-summary">
            <h3>Financial Summary</h3>
            <p>Annual Income: ${plaidData.annual_income.toLocaleString()}</p>
            <p>Current Debt: ${plaidData.total_debt.toLocaleString()}</p>
            <p>Credit Score: {plaidData.credit_score}</p>
          </div>
        )}
      </div>

      <form onSubmit={handleSubmit}>
        <div className="form-group">
          <label>Loan Amount:</label>
          <input
            type="number"
            name="loan_amount"
            value={formData.loan_amount}
            onChange={handleChange}
            placeholder={`Max ${(propertyPrice * 0.8).toLocaleString()}`}
            required
          />
        </div>

        <div className="form-group">
          <label>Down Payment:</label>
          <input
            type="number"
            name="down_payment"
            value={formData.down_payment}
            onChange={handleChange}
            placeholder={`Min ${(propertyPrice * 0.2).toLocaleString()}`}
            required
          />
        </div>

        <button type="submit" disabled={loading || !plaidData}>
          {loading ? 'Analyzing...' : 'Analyze Loan'}
        </button>
      </form>

      {result && (
        <div className="result">
          <pre>{result}</pre>
        </div>
      )}
    </div>
  );
}

MortgageBot.propTypes = {
  onClose: PropTypes.func.isRequired,
  propertyPrice: PropTypes.number,
  propertyAddress: PropTypes.string
};

export default MortgageBot;