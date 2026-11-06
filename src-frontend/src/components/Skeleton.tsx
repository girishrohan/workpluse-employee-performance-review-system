import { cn } from '@/utils';

interface SkeletonProps {
  className?: string;
  height?: string;
  width?: string | number;
  circles?: boolean;
}

export const Skeleton = ({ className, height, width, circles = false }: SkeletonProps) => {
  const baseClasses = 'animate-pulse bg-gray-200 rounded';

  if (circles) {
    return (
      <div
        className={cn('rounded-full bg-gray-200 animate-pulse', className)}
        style={{ height, width }}
      />
    );
  }

  return (
    <div
      className={baseClasses}
      style={{ height, width }}
    />
  );
};

interface TableSkeletonProps {
  rows?: number;
  columns?: number;
}

export const TableSkeleton = ({ rows = 5, columns = 4 }: TableSkeletonProps) => {
  return (
    <div className="space-y-3">
      {Array.from({ length: rows }, (_, i) => (
        <div key={i} className="flex items-center space-x-4">
          {Array.from({ length: columns }, (_, j) => (
            <Skeleton
              key={j}
              height="h-4"
              width={j === 0 ? 'w-24' : 'w-full'}
            />
          ))}
        </div>
      ))}
    </div>
  );
};