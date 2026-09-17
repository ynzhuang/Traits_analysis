import { Criterion, Trait, TraitLevelAgreement, ReviewerDecomposition } from '@/lib/types';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from '@/components/ui/table';
import { Badge } from '@/components/ui/badge';
import { createKappaScore, formatKappa, getKappaLabel } from '@/lib/kappa-utils';
import { cn } from '@/lib/utils';

interface AgreementComparisonTableProps {
  criterion: Criterion;
  reviewers: string[];
  decompositions: Record<string, ReviewerDecomposition>;
  traitAgreements: TraitLevelAgreement[];
  trialId: string;
}

export function AgreementComparisonTable({
  criterion,
  reviewers,
  decompositions,
  traitAgreements,
  trialId
}: AgreementComparisonTableProps) {
  // Get all unique trait signatures from all reviewers for this criterion
  const allTraitSignatures = new Set<string>();
  
  reviewers.forEach(reviewer => {
    const reviewerTrial = decompositions[reviewer]?.[trialId];
    if (reviewerTrial) {
      const matchingCriterion = reviewerTrial.criteria.find(
        c => c.original_text === criterion.original_text
      );
      if (matchingCriterion) {
        matchingCriterion.traits.forEach(trait => {
          const signature = `${trait.trait}|${trait.category}|${trait.value}`;
          allTraitSignatures.add(signature);
        });
      }
    }
  });

  // Add consensus traits from agreement analysis
  traitAgreements.forEach(agreement => {
    allTraitSignatures.add(agreement.trait_signature);
  });

  const sortedTraitSignatures = Array.from(allTraitSignatures).sort();

  // Helper function to get trait for a reviewer
  const getReviewerTrait = (reviewer: string, traitSignature: string): Trait | null => {
    const reviewerTrial = decompositions[reviewer]?.[trialId];
    if (!reviewerTrial) return null;
    
    const matchingCriterion = reviewerTrial.criteria.find(
      c => c.original_text === criterion.original_text
    );
    if (!matchingCriterion) return null;

    return matchingCriterion.traits.find(trait => {
      const signature = `${trait.trait}|${trait.category}|${trait.value}`;
      return signature === traitSignature;
    }) || null;
  };

  // Helper function to get agreement data for a trait
  const getTraitAgreement = (traitSignature: string): TraitLevelAgreement | null => {
    return traitAgreements.find(agreement => 
      agreement.trait_signature === traitSignature
    ) || null;
  };

  return (
    <Card className="mb-6">
      <CardHeader>
        <CardTitle className="text-lg">
          <div className="flex items-center gap-2">
            <Badge variant={criterion.type === 'inclusion' ? 'default' : 'destructive'}>
              {criterion.type}
            </Badge>
            Reviewer Comparison
          </div>
        </CardTitle>
        <p className="text-sm text-gray-600 mt-2">
          {criterion.original_text}
        </p>
      </CardHeader>
      <CardContent>
        <div className="overflow-x-auto">
          <Table>
            <TableHeader>
              <TableRow>
                <TableHead className="w-64">Trait Signature</TableHead>
                <TableHead className="w-24 text-center">Agreement</TableHead>
                {reviewers.map(reviewer => (
                  <TableHead key={reviewer} className="text-center min-w-32">
                    {reviewer}
                  </TableHead>
                ))}
              </TableRow>
            </TableHeader>
            <TableBody>
              {sortedTraitSignatures.map(traitSignature => {
                const agreement = getTraitAgreement(traitSignature);
                const kappaScore = agreement ? createKappaScore(agreement.fleiss_kappa) : null;
                
                return (
                  <TableRow key={traitSignature}>
                    <TableCell className="font-mono text-sm">
                      <div className="space-y-1">
                        <div className="font-medium">
                          {traitSignature.split('|')[0]}
                        </div>
                        <div className="text-xs text-gray-500">
                          {traitSignature.split('|')[1]} • {traitSignature.split('|')[2]}
                        </div>
                      </div>
                    </TableCell>
                    <TableCell className="text-center">
                      {kappaScore ? (
                        <div className="space-y-1">
                          <Badge 
                            variant="outline" 
                            className={cn("text-xs", kappaScore.color)}
                          >
                            {formatKappa(kappaScore.value)}
                          </Badge>
                          <div className="text-xs text-gray-500">
                            {getKappaLabel(kappaScore.interpretation)}
                          </div>
                        </div>
                      ) : (
                        <span className="text-xs text-gray-400">N/A</span>
                      )}
                    </TableCell>
                    {reviewers.map(reviewer => {
                      const trait = getReviewerTrait(reviewer, traitSignature);
                      return (
                        <TableCell key={reviewer} className="text-center">
                          {trait ? (
                            <div className="space-y-1">
                              <Badge variant="secondary" className="text-xs">
                                ✓
                              </Badge>
                              {trait.source_text && (
                                <div className="text-xs text-gray-500 max-w-32 truncate">
                                  &ldquo;{trait.source_text}&rdquo;
                                </div>
                              )}
                            </div>
                          ) : (
                            <Badge variant="outline" className="text-xs text-gray-400">
                              —
                            </Badge>
                          )}
                        </TableCell>
                      );
                    })}
                  </TableRow>
                );
              })}
            </TableBody>
          </Table>
        </div>
        
        {sortedTraitSignatures.length === 0 && (
          <div className="text-center py-8 text-gray-500">
            No traits found for this criterion
          </div>
        )}
      </CardContent>
    </Card>
  );
}