import React from 'react';

interface ResultTableProps {
  rows: Array<Record<string, any>>;
  columnNames: string[];
}

const ResultTable: React.FC<ResultTableProps> = ({ rows, columnNames }) => {
  if (!rows || rows.length === 0) {
    return (
      <div className="text-gray-500 text-center py-8">
        No results to display
      </div>
    );
  }

  return (
    <div className="w-full overflow-hidden border border-gray-300 rounded-lg shadow-sm">
      <div className="overflow-x-auto overflow-y-auto max-h-96">
        <table className="min-w-full divide-y divide-gray-200">
          <thead className="bg-gray-50 sticky top-0 z-10">
            <tr>
              {columnNames.map((column, index) => (
                <th
                  key={index}
                  className="px-4 py-3 text-left text-xs font-semibold text-gray-700 uppercase tracking-wider border-r border-gray-200 last:border-r-0"
                >
                  {column}
                </th>
              ))}
            </tr>
          </thead>
          <tbody className="bg-white divide-y divide-gray-200">
            {rows.map((row, rowIndex) => (
              <tr
                key={rowIndex}
                className={rowIndex % 2 === 0 ? 'bg-white' : 'bg-gray-50'}
              >
                {columnNames.map((column, colIndex) => (
                  <td
                    key={colIndex}
                    className="px-4 py-3 text-sm text-gray-900 border-r border-gray-200 last:border-r-0 whitespace-nowrap"
                  >
                    {row[column] !== null && row[column] !== undefined
                      ? String(row[column])
                      : '—'}
                  </td>
                ))}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      <div className="bg-gray-50 px-4 py-2 border-t border-gray-200">
        <p className="text-xs text-gray-600">
          Showing {rows.length} row{rows.length !== 1 ? 's' : ''}
        </p>
      </div>
    </div>
  );
};

export default ResultTable;
