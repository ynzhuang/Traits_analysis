import { Trial } from '@/lib/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

interface TrialHeaderProps {
  trial: Trial;
  reviewers: string[];
}

export function TrialHeader({ trial, reviewers }: TrialHeaderProps) {
  return (
    <Card className="mb-6">
      <CardHeader>
        <CardTitle className="flex items-center justify-between">
          <span>Trial: {trial.trial_id}</span>
          <Badge variant="outline" className="text-sm">
            {reviewers.length} Reviewers
          </Badge>
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <h3 className="font-semibold text-sm text-gray-600 mb-2">Criteria Summary</h3>
            <div className="space-y-1">
              <div className="flex justify-between">
                <span className="text-sm">Total Criteria:</span>
                <span className="font-medium">{trial.criteria.length}</span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm">Inclusion:</span>
                <span className="font-medium">
                  {trial.criteria.filter(c => c.type === 'inclusion').length}
                </span>
              </div>
              <div className="flex justify-between">
                <span className="text-sm">Exclusion:</span>
                <span className="font-medium">
                  {trial.criteria.filter(c => c.type === 'exclusion').length}
                </span>
              </div>
            </div>
          </div>
          <div>
            <h3 className="font-semibold text-sm text-gray-600 mb-2">Reviewers</h3>
            <div className="flex flex-wrap gap-2">
              {reviewers.map((reviewer) => (
                <Badge key={reviewer} variant="secondary" className="text-xs">
                  {reviewer}
                </Badge>
              ))}
            </div>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}