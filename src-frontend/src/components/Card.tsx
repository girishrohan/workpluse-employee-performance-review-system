import React from 'react';
import { cn } from '@/utils';

interface CardProps {
  className?: string;
  children: React.ReactNode;
  header?: React.ReactNode;
  footer?: React.ReactNode;
  padding?: 'none' | 'sm' | 'md' | 'lg' | 'xl';
  hover?: boolean;
}

export const Card = React.forwardRef<HTMLDivElement, CardProps>(
  ({ className, children, header, footer, padding = 'md', hover = false }, ref) => {
    const paddingClasses = {
      none: '',
      sm: 'p-4',
      md: 'p-6',
      lg: 'p-8',
      xl: 'p-10',
    };

    return (
      <div
        ref={ref}
        className={cn(
          'rounded-xl bg-white border border-gray-200',
          'shadow-sm hover:shadow-md transition-shadow duration-200',
          hover && 'hover:shadow-lg',
          paddingClasses[padding],
          className
        )}
      >
        {header && (
          <div className="mb-4 border-b border-gray-200 pb-4 last:mb-0 last:border-b-0">
            {header}
          </div>
        )}
        <div>{children}</div>
        {footer && (
          <div className="mt-4 border-t border-gray-200 pt-4 first:mt-0 first:border-t-0">
            {footer}
          </div>
        )}
      </div>
    );
  }
);

Card.displayName = 'Card';

interface StatsCardProps {
  title: string;
  value: string | number;
  change?: string;
  changeType?: 'increase' | 'decrease' | 'neutral';
  icon?: React.ReactNode;
  description?: string;
}

export const StatsCard = ({
  title,
  value,
  change,
  changeType = 'neutral',
  icon,
  description,
}: StatsCardProps) => {
  const changeClasses = {
    increase: 'text-green-600',
    decrease: 'text-red-600',
    neutral: 'text-gray-500',
  };

  return (
    <Card className="hover:shadow-md transition-shadow duration-200">
      <div className="flex items-start justify-between">
        <div className="space-y-1">
          <p className="text-sm font-medium text-gray-600">{title}</p>
          <p className="text-2xl font-bold text-gray-900">{value}</p>
          {change && (
            <p className={cn('text-xs', changeClasses[changeType])}>
              {change}
            </p>
          )}
        </div>
        {icon && (
          <div className="flex h-12 w-12 items-center justify-center rounded-lg bg-teal-50 text-teal-600">
            {icon}
          </div>
        )}
      </div>
      {description && <p className="mt-2 text-xs text-gray-500">{description}</p>}
    </Card>
  );
};