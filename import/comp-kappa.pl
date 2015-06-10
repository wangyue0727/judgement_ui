use strict;
use warnings;

my $usage = "\nperl comp-kappa.pl results_from_assessment\n\n";

my $result_file = shift or die $usage;

my %query2assessor_map=();
my %document_qrel=();
my %aspect_qrel=();
my %aspect_qrel_count=();
open(FILE,"$result_file") or die "Cannot open the $result_file: $!\n";
while(defined(my $line=<FILE>)){
	chomp($line);
	my @elements = split(" ",$line);
	if (scalar(@elements) ne 9){
		print "Wrong result format: $line\n";
		next;
	}
	next if $elements[8] eq "N/A";
	my $qid = $elements[0];
	my $did = $elements[2];
	my $sid = $elements[3];
	my $judgement = $elements[4];
	my $aspect = $elements[5];
	my $keywords = $elements[6];
	my $doc_bug = $elements[7];
	my $assessor = $elements[8];

	my $index = "$did-$sid";

	$query2assessor_map{$qid}{$assessor} = 1;
	$document_qrel{$assessor}{$did} = $doc_bug;
	$aspect_qrel{$assessor}{$index} = $aspect;
	if (exists($aspect_qrel_count{$assessor}{$qid}{$aspect})){
		$aspect_qrel_count{$assessor}{$qid}{$aspect} += 1;
	} else {
		$aspect_qrel_count{$assessor}{$qid}{$aspect} = 1;
	}

}

my $counter=0;
my $avg_doc=0;
my $avg_sent_bi=0;
my $avg_sent_mul=0;
foreach my $qid (keys %query2assessor_map){
	if (keys %{$query2assessor_map{$qid}} > 1){

		my @assessors = keys %{$query2assessor_map{$qid}};
		my $assessor1 = $assessors[0];
		my $assessor2 = $assessors[1];
		$counter++;
		my $score = compute_doc_level_kappa($assessor1,$assessor2);
		$avg_doc+=$score;
		printf "The doc level kappa coff of $assessor1 and $assessor2 is: %.3f\n", $score;

		$score = compute_sentence_level_kappa_binary($assessor1,$assessor2);
		$avg_sent_bi+=$score;
		printf "The sentence level (binary) kappa coff of $assessor1 and $assessor2 is: %.3f\n", $score;
		
		$score = compute_sentence_level_kappa_multi($assessor1,$assessor2);
		$avg_sent_mul+=$score;
		printf "The sentence level (multiple) kappa coff of $assessor1 and $assessor2 is: %.3f\n", $score;
	}
}

if ($counter ne 0){
	printf "The average doc level kappa coff is: %.3f\n",($avg_doc/$counter);
	printf "The average sentence level (binary) kappa coff is: %.3f\n",($avg_sent_bi/$counter);
	printf "The average sentence level (multiple) kappa coff is: %.3f\n",($avg_sent_mul/$counter);
}

sub compute_sentence_level_kappa_multi {
	my $first = $_[0];
	my $second = $_[1];

	my $total = 0;
	my $same = 0;
	my $different = 0;
	my $firstyes = 0;
	my $secondyes = 0;
	my $firstno = 0;
	my $secondno = 0;

	
	foreach my $index (keys %{$aspect_qrel{$first}}){
		if(exists($aspect_qrel{$second}{$index})){
			$total++;
			if ($aspect_qrel{$second}{$index} eq $aspect_qrel{$first}{$index}){
				$same++;
			} else {
				$different++;
			}
		}
	}
	my $Pre = 0;
	foreach my $qid (keys %{$aspect_qrel_count{$first}}){
		foreach my $aspect (keys %{$aspect_qrel_count{$first}{$qid}}){
			if (exists($aspect_qrel_count{$second}{$qid}{$aspect})){
				$Pre += $aspect_qrel_count{$second}{$qid}{$aspect}*$aspect_qrel_count{$first}{$qid}{$aspect};
			}
		}				
	}
	$Pre = $Pre / $total / $total;
	my $Pra = $same/$total;

	my $k = ($Pra-$Pre)/(1-$Pre);	
	return $k;
}

sub compute_sentence_level_kappa_binary{
	my $first = $_[0];
	my $second = $_[1];

	my $total = 0;
	my $same = 0;
	my $different = 0;
	my $firstyes = 0;
	my $secondyes = 0;
	my $firstno = 0;
	my $secondno = 0;

	foreach my $index (keys %{$aspect_qrel{$first}}){
		if(exists($aspect_qrel{$second}{$index})){
			$total++;
			if ($aspect_qrel{$second}{$index} eq "None" and $aspect_qrel{$first}{$index} eq "None"){
				$same++;
			} elsif ($aspect_qrel{$second}{$index} ne "None" and $aspect_qrel{$first}{$index} ne "None") {
				$same++;
			} else {
				$different++;
			}
			if ($aspect_qrel{$second}{$index} ne "None" ){
				$secondyes++;
			} else {
				$secondno++;
			}
			if ($aspect_qrel{$first}{$index} ne "None" ){
				$firstyes++;
			} else {
				$firstno++;
			}
		}
	}
	my $Pra = $same/$total;
	my $Pre = ($firstyes / $total) * ($secondyes / $total) + ($firstno / $total) * ($secondno / $total);

	my $k = ($Pra-$Pre)/(1-$Pre);	
	return $k;
}

sub compute_doc_level_kappa{
	my $first = $_[0];
	my $second = $_[1];

	my $total = 0;
	my $same = 0;
	my $different = 0;
	my $firstyes = 0;
	my $secondyes = 0;
	my $firstno = 0;
	my $secondno = 0;

	foreach my $did (keys %{$document_qrel{$first}}){
		if(exists($document_qrel{$second}{$did})){
			$total++;
			if ($document_qrel{$second}{$did} == $document_qrel{$first}{$did}){
				$same++;
			} else {
				$different++;
			}
			if ($document_qrel{$second}{$did} == 1){
				$secondyes++;
			} else {
				$secondno++;
			}
			if ($document_qrel{$first}{$did} == 1){
				$firstyes++;
			} else {
				$firstno++;
			}
		}
	}
	my $Pra = $same/$total;
	my $Pre = ($firstyes / $total) * ($secondyes / $total) + ($firstno / $total) * ($secondno / $total);

	my $k = ($Pra-$Pre)/(1-$Pre);	
	return $k;
}