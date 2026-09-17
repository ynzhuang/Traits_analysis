import { TraitLevelAgreement, AgreementSummary } from '@/lib/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { createKappaScore, formatKappa, getKappaLabel } from '@/lib/kappa-utils';
import { cn } from '@/lib/utils';

interface ConsensusPanelProps {
  traitAgreements: TraitLevelAgreement[];
  overallSummary: AgreementSummary['overall'];
}

export function ConsensusPanel({ traitAgreements, overallSummary }: ConsensusPanelProps) {
  // Sort traits by kappa score (highest agreement first)
  const sortedTraits = [...traitAgreements].sort((a, b) => b.fleiss_kappa - a.fleiss_kappa);
  
  // Group traits by agreement level
  const groupedTraits = {
    high: sortedTraits.filter(t => t.fleiss_kappa >= 0.6),
    moderate: sortedTraits.filter(t => t.fleiss_kappa >= 0.4 && t.fleiss_kappa < 0.6),
    low: sortedTraits.filter(t => t.fleiss_kappa < 0.4)
  };

  const overallKappaScore = createKappaScore(overallSummary.overall_fleiss_kappa);

  return (
    <div className="space-y-6">
      {/* Overall Summary */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center justify-between">
            <span>Overall Agreement Summary</span>
            <Badge 
              variant="outline" 
              className={cn("text-sm", overallKappaScore.color)}
            >
              κ = {formatKappa(overallKappaScore.value)} ({getKappaLabel(overallKappaScore.interpretation)})
            </Badge>
          </CardTitle>
        </CardHeader>
        <CardContent>
          <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
            <div className="text-center">
              <div className="text-2xl font-bold text-blue-600">
                {overallSummary.total_traits}
              </div>
              <div className="text-sm text-gray-600">Total Traits</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-green-600">
                {overallSummary.total_reviewers}
              </div>
              <div className="text-sm text-gray-600">Reviewers</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-purple-600">
                {formatKappa(overallSummary.average_trait_kappa)}
              </div>
              <div className="text-sm text-gray-600">Avg Trait κ</div>
            </div>
            <div className="text-center">
              <div className="text-2xl font-bold text-orange-600">
                {formatKappa(overallSummary.average_criterion_kappa)}
              </div>
              <div className="text-sm text-gray-600">Avg Criterion κ</div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* High Agreement Traits */}
      {groupedTraits.high.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Badge variant="default" className="bg-green-100 text-green-800">
                High Agreement
              </Badge>
              <span className="text-lg">Substantial to Perfect (κ ≥ 0.6)</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {groupedTraits.high.map((trait, index) => {
                const kappaScore = createKappaScore(trait.fleiss_kappa);
                return (
                  <div key={index} className="flex items-center justify-between p-3 bg-green-50 rounded-lg border border-green-200">
                    <div className="flex-1">
                      <div className="font-mono text-sm font-medium">
                        {trait.trait_signature}
                      </div>
                      <div className="text-xs text-gray-600 mt-1">
                        {trait.present_instances}/{trait.total_possible_instances} reviewers agreed • 
                        {trait.consensus_method} consensus
                      </div>
                    </div>
                    <Badge 
                      variant="outline" 
                      className={cn("ml-3", kappaScore.color)}
                    >
                      κ = {formatKappa(kappaScore.value)}
                    </Badge>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Moderate Agreement Traits */}
      {groupedTraits.moderate.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Badge variant="default" className="bg-yellow-100 text-yellow-800">
                Moderate Agreement
              </Badge>
              <span className="text-lg">Fair to Moderate (0.4 ≤ κ &lt; 0.6)</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {groupedTraits.moderate.map((trait, index) => {
                const kappaScore = createKappaScore(trait.fleiss_kappa);
                return (
                  <div key={index} className="flex items-center justify-between p-3 bg-yellow-50 rounded-lg border border-yellow-200">
                    <div className="flex-1">
                      <div className="font-mono text-sm font-medium">
                        {trait.trait_signature}
                      </div>
                      <div className="text-xs text-gray-600 mt-1">
                        {trait.present_instances}/{trait.total_possible_instances} reviewers agreed • 
                        {trait.consensus_method} consensus
                      </div>
                    </div>
                    <Badge 
                      variant="outline" 
                      className={cn("ml-3", kappaScore.color)}
                    >
                      κ = {formatKappa(kappaScore.value)}
                    </Badge>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {/* Low Agreement Traits */}
      {groupedTraits.low.length > 0 && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <Badge variant="destructive" className="bg-red-100 text-red-800">
                Low Agreement
              </Badge>
              <span className="text-lg">Poor to Slight (κ &lt; 0.4)</span>
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="space-y-3">
              {groupedTraits.low.map((trait, index) => {
                const kappaScore = createKappaScore(trait.fleiss_kappa);
                return (
                  <div key={index} className="flex items-center justify-between p-3 bg-red-50 rounded-lg border border-red-200">
                    <div className="flex-1">
                      <div className="font-mono text-sm font-medium">
                        {trait.trait_signature}
                      </div>
                      <div className="text-xs text-gray-600 mt-1">
                        {trait.present_instances}/{trait.total_possible_instances} reviewers agreed • 
                        {trait.consensus_method} consensus
                      </div>
                    </div>
                    <Badge 
                      variant="outline" 
                      className={cn("ml-3", kappaScore.color)}
                    >
                      κ = {formatKappa(kappaScore.value)}
                    </Badge>
                  </div>
                );
              })}
            </div>
          </CardContent>
        </Card>
      )}

      {traitAgreements.length === 0 && (
        <Card>
          <CardContent className="text-center py-8 text-gray-500">
            No consensus data available
          </CardContent>
        </Card>
      )}
    </div>
  );
}