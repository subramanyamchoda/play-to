// src/App.jsx
import { useEffect, useState } from "react";
import api from "./api";

import BalanceCard from "./components/BalanceCard";
import PayoutForm from "./components/PayoutForm";
import PayoutTable from "./components/PayoutTable";

export default function App() {
  const [merchantId, setMerchantId] = useState(1);

  const [data, setData] = useState({
    available_balance: 0,
    held_balance: 0,
    recent_payouts: [],
  });

  const fetchData = async () => {
    try {
      const res = await api.get(
        `/v1/dashboard?merchant_id=${merchantId}`
      );

      setData(res.data);
    } catch (error) {
      console.error(error);
    }
  };

  useEffect(() => {
    fetchData();

    const timer = setInterval(fetchData, 3000);

    return () => clearInterval(timer);
  }, [merchantId]);

  return (
    <div className="max-w-6xl mx-auto p-8">
      <h1 className="text-3xl font-bold mb-8">
        Playto Merchant Dashboard
      </h1>

      {/* Merchant Selector */}
      <div className="bg-white p-5 rounded-xl shadow mb-6">
        <label className="mr-3 font-medium">
          Select Merchant:
        </label>

        <select
          value={merchantId}
          onChange={(e) =>
            setMerchantId(Number(e.target.value))
          }
          className="border p-2 rounded"
        >
          <option value={1}>Rahul Agency</option>
          <option value={2}>Aman Freelance</option>
          <option value={3}>Sita Digital</option>
          </select>
      </div>

      <div className="grid md:grid-cols-2 gap-4 mb-6">
        <BalanceCard
          title="Available Balance"
          value={data.available_balance}
        />

        <BalanceCard
          title="Held Balance"
          value={data.held_balance}
        />
      </div>

      <div className="mb-6">
        <PayoutForm
          merchantId={merchantId}
          refresh={fetchData}
        />
      </div>

      <PayoutTable payouts={data.recent_payouts} />
    </div>
  );
}