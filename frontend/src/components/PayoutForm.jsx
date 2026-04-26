import { useState } from "react";
import axios from "axios";

export default function PayoutForm({ merchantId, refresh }) {
  const [amount, setAmount] = useState("");
  const [loading, setLoading] = useState(false);

  const submit = async () => {
    if (!amount || Number(amount) <= 0) {
      alert("Enter a valid amount");
      return;
    }

    setLoading(true);

    try {
      await axios.post(
        "https://play-to.onrender.com/api/v1/payouts",
        {
          merchant_id: merchantId,
          amount_paise: Math.floor(Number(amount) * 100),
          bank_account_id: "bank_test_001"
        },
        {
          headers: {
            "Content-Type": "application/json",
            "Idempotency-Key": crypto.randomUUID()
          }
        }
      );

      alert("Payout Requested");
      setAmount("");
      refresh();
    } catch (err) {
      console.log(err.response?.data || err.message);
      alert(err.response?.data?.error || "Something went wrong");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white p-5 rounded-xl shadow">
      <h2 className="font-semibold mb-4">Request Payout</h2>

      <input
        type="number"
        placeholder="Enter amount in ₹"
        value={amount}
        onChange={(e) => setAmount(e.target.value)}
        className="border p-2 rounded w-full mb-3"
      />

      <button
        onClick={submit}
        disabled={loading}
        className={`px-4 py-2 rounded text-white ${
          loading ? "bg-gray-400" : "bg-blue-600 hover:bg-blue-700"
        }`}
      >
        {loading ? "Processing..." : "Withdraw"}
      </button>
    </div>
  );
}
