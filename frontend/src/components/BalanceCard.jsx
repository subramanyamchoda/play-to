// src/components/BalanceCard.jsx
export default function BalanceCard({
  title,
  value,
}) {
  return (
    <div className="bg-white p-5 rounded-xl shadow">
      <h3 className="text-gray-500 text-sm">
        {title}
      </h3>

      <p className="text-2xl font-bold mt-2">
        ₹ {(value / 100).toFixed(2)}
      </p>
    </div>
  );
}