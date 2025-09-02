import { ChatContext } from '@/app/chat-context';
import { ChartData } from '@/types/chat';
import { Chart } from '@berryv/g2-react';
import { useContext, useMemo } from 'react';

export default function BarChart({ chart }: { key: string; chart: ChartData }) {
  const { mode } = useContext(ChatContext);

  // Process data to ensure numeric values for proper y-axis ordering
  const processedChart = useMemo(() => {
    const processedValues = chart.values
      .map(item => ({
        ...item,
        value: typeof item.value === 'string' ? parseFloat(item.value) || 0 : item.value,
      }))
      // Sort by value in descending order for better visualization
      .sort((a, b) => b.value - a.value);

    // Global cap: keep only the first 10 unique x categories (name)
    const seen = new Set<string>();
    const keepNames: string[] = [];
    for (const row of processedValues) {
      const key = String(row.name);
      if (!seen.has(key)) {
        seen.add(key);
        keepNames.push(key);
        if (keepNames.length >= 10) break;
      }
    }
    const limitedValues = processedValues.filter(r => keepNames.includes(String(r.name)));

    return {
      ...chart,
      values: limitedValues,
    };
  }, [chart]);

  // Smart number formatter: show integers as integers, decimals with 2 decimal places
  const formatNumber = (value: any) => {
    const num = Number(value);
    return Number.isInteger(num) ? num.toString() : num.toFixed(2);
  };

  return (
    <div className='flex-1 min-w-0 p-4 bg-white dark:bg-theme-dark-container rounded'>
      <div className='h-full'>
        <div className='mb-2'>{chart.chart_name}</div>
        <div className='opacity-80 text-sm mb-2'>{chart.chart_desc}</div>
        <div className='h-[300px]'>
          <Chart
            style={{ height: '100%' }}
            options={{
              autoFit: true,
              theme: mode,
              type: 'interval',
              data: processedChart.values,
              encode: { x: 'name', y: 'value', color: 'type' },
              axis: {
                x: {
                  title: false,
                },
                y: {
                  labelFormatter: formatNumber,
                  title: false,
                },
              },
              tooltip: {
                items: [
                  {
                    field: 'name',
                    name: 'name',
                  },
                  {
                    field: 'value',
                    name: 'Value',
                    valueFormatter: formatNumber,
                  },
                ],
              },
              scale: {
                value: { type: 'linear' },
              },
            }}
          />
        </div>
      </div>
    </div>
  );
}
