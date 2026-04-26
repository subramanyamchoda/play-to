// src/components/PayoutTable.jsx
export default function PayoutTable({ payouts }) {
  return (
    <div className="bg-white p-5 rounded-xl shadow">
      <h2 className="font-semibold mb-4">
        Recent Payouts
      </h2>

      <table className="w-full text-left">
        <thead>
          <tr className="border-b">
            <th className="py-2">ID</th>
            <th className="py-2">Amount</th>
            <th className="py-2">Status</th>
          </tr>
        </thead>

        <tbody>
          {payouts.length > 0 ? (
            payouts.map((p) => (
              <tr
                key={p.id}
                className="border-b"
              >
                <td className="py-2">{p.id}</td>

                <td className="py-2">
                  ₹ {(p.amount_paise / 100).toFixed(2)}
                </td>

                <td className="py-2 capitalize">
                  {p.status}
                </td>
              </tr>
            ))
          ) : (
            <tr>
              <td
                colSpan="3"
                className="py-4 text-gray-500"
              >
                No payouts yet
              </td>
            </tr>
          )}
        </tbody>
      </table>
    </div>
  );
}