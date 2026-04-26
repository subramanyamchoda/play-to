// src/components/PayoutForm.jsx
import { useState } from "react";
import api from "../api";

export default function PayoutForm({
  merchantId,
  refresh,
}) {
  const [amount, setAmount] = useState("");

  const submit = async () => {
    try {
      const uuid = crypto.randomUUID();

      await api.post(
        "/v1/payouts",
        {
          merchant_id: merchantId,
          amount_paise: Number(amount) * 100,
          bank_account_id: merchantId,
        },
        {
          headers: {
            "Idempotency-Key": uuid,
          },
        }
      );

      alert("Payout Requested");
      setAmount("");
      refresh();
    } catch (err) {
      alert(
        err.response?.data?.error ||
          "Something went wrong"
      );
    }
  };

  return (
    <div className="bg-white p-5 rounded-xl shadow">
      <h2 className="font-semibold mb-4">
        Request Payout
      </h2>

      <input
        type="number"
        placeholder="Enter amount in ₹"
        value={amount}
        onChange={(e) =>
          setAmount(e.target.value)
        }
        className="border p-2 rounded w-full mb-3"
      />

      <button
        onClick={submit}
        className="bg-blue-600 text-white px-4 py-2 rounded hover:bg-blue-700"
      >
        Withdraw
      </button>
    </div>
  );
}