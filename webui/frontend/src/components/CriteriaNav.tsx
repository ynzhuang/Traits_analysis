import { Criterion } from '@/lib/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { cn } from '@/lib/utils';

interface CriteriaNavProps {
  criteria: Criterion[];
  activeCriterionIndex: number;
  onCriterionSelect: (index: number) => void;
}

export function CriteriaNav({ 
  criteria, 
  activeCriterionIndex, 
  onCriterionSelect 
}: CriteriaNavProps) {
  return (
    <Card className="h-fit sticky top-4">
      <CardHeader>
        <CardTitle className="text-lg">Criteria Navigation</CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <div className="max-h-96 overflow-y-auto">
          {criteria.map((criterion, index) => (
            <button
              key={index}
              onClick={() => onCriterionSelect(index)}
              className={cn(
                "w-full text-left p-3 border-b border-gray-100 hover:bg-gray-50 transition-colors",
                activeCriterionIndex === index && "bg-blue-50 border-l-4 border-l-blue-500"
              )}
            >
              <div className="flex items-start justify-between gap-2">
                <div className="flex-1 min-w-0">
                  <div className="flex items-center gap-2 mb-1">
                    <Badge 
                      variant={criterion.type === 'inclusion' ? 'default' : 'destructive'}
                      className="text-xs"
                    >
                      {criterion.type}
                    </Badge>
                    <span className="text-xs text-gray-500">#{index + 1}</span>
                  </div>
                  <p className="text-sm text-gray-700 line-clamp-2">
                    {criterion.original_text}
                  </p>
                  <div className="flex items-center gap-2 mt-1">
                    <span className="text-xs text-gray-500">
                      {criterion.traits.length} traits
                    </span>
                  </div>
                </div>
              </div>
            </button>
          ))}
        </div>
      </CardContent>
    </Card>
  );
}