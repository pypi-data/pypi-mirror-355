#!/usr/bin/env python3
import os

import pytest

from rush import Provider
from rush.graphql_client.benchmark import BenchmarkBenchmark
from rush.graphql_client.benchmarks import BenchmarksBenchmarksEdgesNode
from rush.graphql_client.create_project import CreateProjectCreateProject
from rush.graphql_client.run_benchmark import RunBenchmarkRunBenchmark
from rush.provider import build_provider_with_functions


@pytest.fixture
async def provider():
    if "RUSH_TOKEN" in os.environ:
        print("initing")
        return await build_provider_with_functions()
    else:
        print(os.environ)
        print("Skipping test_provider_init")
        return Provider("")


@pytest.fixture
async def project(provider: Provider):
    p = await provider.create_project("test")
    yield p
    await provider.client.delete_project(p.id)


@pytest.fixture
async def benchmark(
    provider: Provider,
) -> BenchmarksBenchmarksEdgesNode | BenchmarkBenchmark:
    return await provider.benchmark(name="OpenFF Protein-Ligand Binding Benchmark")


@pytest.fixture(scope="function")
async def benchmark_submission(
    provider: Provider,
    benchmark: BenchmarksBenchmarksEdgesNode,
) -> RunBenchmarkRunBenchmark:
    return await provider.run_benchmark(
        benchmark.id,
        "\\i -> (outputs i)",
        "echo submission",
        sample=0.2,
        with_outs=True,
    )


@pytest.fixture(scope="function")
async def openff_real_benchmark_submission(
    provider: Provider, benchmark: BenchmarksBenchmarksEdgesNode
) -> RunBenchmarkRunBenchmark:
    rex = """
let
    runspec = RunSpec {
        target = 'Bullet',
        resources = Resources {
            storage = some 10,
            storage_units = some "MB",
            gpus = some 1
        }
    },

    runspec_nogpu = RunSpec {
        target = 'Bullet',
        resources = Resources {
            storage = some 10,
            storage_units = some "MB",
            gpus = none
        }
    },

    auto3d = \\smi ->
        let
            result = get 0 (get "Ok" (get 0 (await (get 1 (
                auto3d_rex runspec { k = 1 } [smi]
            ))))),
            make_virtual_object = \\index ->
                VirtualObject {
                    path = get "path" (get index result),
                    size = get "size" (get index result),
                    format = "json"
                }
        in
            (make_virtual_object 0, make_virtual_object 1),

    p2rank = \\prot_conf ->
        let
            result = get 0 (await (get 1 (
                p2rank_rex runspec_nogpu {} prot_conf
            )))
        in
            get "Ok" result,

    gnina = \\prot_conf -> \\bounding_box -> \\smol_conf ->
        let
            result = gnina_rex runspec {} [prot_conf] [bounding_box] smol_conf [],
            processed = get 0 (get "Ok" (get 0 (await (get 1 result))))
        in
            get 0 processed

in
\\input ->
    let
        protein = load (id (get 0 input)) 'ProteinConformer',
        smol_id = id (get 1 input),
        smiles = smi (load smol_id 'Smol'),

        structure = load (structure_id protein) 'Structure',
        trc = [
            topology structure,
            residues structure,
            chains structure
        ],

        bounding_box = get 0 (get 0 (p2rank trc)),

        smol_structure = auto3d smiles,

        docked_structure = gnina trc bounding_box [smol_structure],

        min_affinity = list_min (map (get "affinity") (get "scores" docked_structure)),

        binding_affinity = BindingAffinity {
            affinity = min_affinity,
            affinity_metric = 'kcal/mol',
            protein_id = protein_id protein,
            smol_id = smol_id,
            metadata = Metadata {
                name = id input,
                description = none,
                tags = [id input]
            }
        }
    in
        [BenchmarkArg {
            entity = "BindingAffinity",
            id = save binding_affinity
        }]
    """

    return await provider.run_benchmark(benchmark.id, rex, "actual submission", sample=0.2)


@pytest.mark.asyncio
async def test_provider_init(provider: Provider):
    assert provider


@pytest.mark.asyncio
async def test_projects(provider: Provider):
    projects_pages = await provider.projects()
    assert projects_pages is not None
    p = []
    async for page in projects_pages:
        for project in page.edges:
            p.append(project)
    assert len(p) > 0


@pytest.mark.asyncio
async def test_create_project(project: CreateProjectCreateProject):
    assert project is not None
    assert project.name == "test"


@pytest.mark.asyncio
async def test_runs(provider: Provider, project: CreateProjectCreateProject):
    provider.set_project(project.id)
    runs = await provider.runs()
    rs = []
    async for run_page in runs:
        for run in run_page.edges:
            rs.append(run)
    # runs should be zero for new project
    assert len(rs) == 0


@pytest.mark.asyncio
async def test_submit_benchmark(benchmark_submission: RunBenchmarkRunBenchmark):
    assert benchmark_submission is not None


@pytest.mark.asyncio
async def test_benchmark_submissions(provider: Provider, benchmark_submission: RunBenchmarkRunBenchmark):
    submissions = await provider.benchmark_submissions()
    ss = []
    async for submission_page in submissions:
        for s in submission_page.edges:
            ss.append(s)
    assert len(ss) > 0


@pytest.mark.asyncio
async def test_poll_benchmark_submission(
    provider: Provider,
    benchmark_submission: RunBenchmarkRunBenchmark,
):
    submission = await provider.poll_benchmark_submission(benchmark_submission.id)
    assert submission is not None
    assert submission.source_run.status == "DONE"
    # wait another 60 seconds for eval to finish
    submission = await provider.poll_benchmark_submission(benchmark_submission.id, with_scores=True)
    assert len(submission.scores.nodes) > 0


@pytest.mark.asyncio
async def test_submit_openff_benchmark(
    openff_real_benchmark_submission: RunBenchmarkRunBenchmark,
):
    assert openff_real_benchmark_submission is not None


@pytest.mark.asyncio
async def test_runs_after_benchmark_submission(
    provider: Provider,
    benchmark_submission: RunBenchmarkRunBenchmark,
):
    runs = await provider.runs()
    rs = []
    async for run_page in runs:
        for run in run_page.edges:
            rs.append(run)
    assert len(rs) == 1


af2rave_rex = """
let
    mmseqs2 = λ config fastas →
        get 0 (mmseqs2_rex_s default_runspec config [fastas]),

    colabfold = λ config msas →
        get 0 (colabfold_rex_s default_runspec_gpu config msas),

    af2rave = λ config conformers →
        get 0 (af2rave_rex_s default_runspec_gpu config [conformers])
in
    let
        protein = Protein {
            sequence = "MGPEALSSLLLLLLVASGDADMKGHFDPAKCRYALGMQDRTIPDSDISASSSWSDSTAARHSRLESSDGDGAWCPAGSVFPKEEEYLQVDLQRLHLVALVGTQGRHAGGLGKEFSRSYRLRYSRDGRRWMGWKDRWGQEVISGNEDPEGVVLKDLGPPMVARLVRFYPRADRVMSVCLRVELYGCLWRDGLLSYTAPVGQTMYLSEAVYLNDSTYDGHTVGGLQYGGLGQLADGVVGLDDFRKSQELRVWPGYDYVGWSNHSFSSGYVEMEFEFDRLRAFQAMQVHCNNMHTLGARLPGGVECRFRRGPAMAWEGEPMRHNLGGNLGDPRARAVSVPLGGRVARFLQCRFLFAGPWLLFSEISFISDVVNNSSPALGGTFPPAPWWPPGPPPTNFSSLELEPRGQQPVAKAEGSPTAILIGCLVAIILLLLLIIALMLWRLHWRRLLSKAERRVLEEELTVHLSVPGDTILINNRPGPREPPPYQEPRPRGNPPHSAPCVPNGSALLLSNPAYRLLLATYARPPRGPGPPTPAWAKPTNTQAYSGDYMEPEKPGAPLLPPPPQNSVPHYAEADIVTLQGVTGGNTYAVPALPPGAVGDGPPRVDFPRSRLRFKEKLGEGQFGEVHLCEVDSPQDLVSLDFPLNVRKGHPLLVAVKILRPDATKNARNDFLKEVKIMSRLKDPNIIRLLGVCVQDDPLCMITDYMENGDLNQFLSAHQLEDKAAEGAPGDGQAAQGPTISYPMLLHVAAQIASGMRYLATLNFVHRDLATRNCLVGENFTIKIADFGMSRNLYAGDYYRVQGRAVLPIRWMAWECILMGKFTTASDVWAFGVTLWEVLMLCRAQPFGQLTDEQVIENAGEFFRDQGRQVYLSRPPACPQGLYELMLRCWSRESEQRPPFSQLHRFLAEDALNTV",
            uniprot_id = some "Q08345",
            metadata = Metadata {
                name = "Epithelial discoidin domain-containing receptor 1",
                description = some "Tyrosine kinase that functions as a cell surface receptor for fibrillar collagen and regulates cell attachment to the extracellular matrix, remodeling of the extracellular matrix, cell migration, differentiation, survival and cell proliferation. Collagen binding triggers a signaling pathway that involves SRC and leads to the activation of MAP kinases. Regulates remodeling of the extracellular matrix by up-regulation of the matrix metalloproteinases MMP2, MMP7 and MMP9, and thereby facilitates cell migration and wound healing. Required for normal blastocyst implantation during pregnancy, for normal mammary gland differentiation and normal lactation. Required for normal ear morphology and normal hearing (By similarity). Promotes smooth muscle cell migration, and thereby contributes to arterial wound healing. Also plays a role in tumor cell invasion. Phosphorylates PTPN11.",
                tags = ["DDR1", "homo sapiens"]
            }
        }
    in
        let
            {- run mmseqs on the protein sequence -}
            msas = mmseqs2
                { }
                (sequence protein),

            {- run colabfold with multiple max_msa values -}
            conformers = colabfold
                {
                    num_recycle = 1,
                    num_seeds = 1, {- 128 -}
                    relax_max_iterations = 200,
                    use_dropout = true,
                    max_msa = "Ms8Mes16"
                }
                msas,

            {- run af2rave-genfeatures on the folded conformers -}
            af2rave_results = af2rave
                {
                    feature_atom_set = [
                        "resid 53 to 82 and name CA",
                        "resid 163 to 225 and name CA",
                        "resid 186 and name CB CG",
                        "resid 186 and name CZ CG",
                        "resid 187 and name O",
                        "resid 73 and name CD",
                        "resid 56 and name CB CZ NZ",
                        "resid 171 and name N"
                    ],
                    feature_rmsd_filter_cutoff_angstroms = 6.0,
                    n_sim_steps = 5000,
                    sim_xtc_freq = 50,
                    sim_cv_freq = 50,
                    spib_neuron_num2 = 256,
                    spib_beta = 0.001
                }
                conformers,

            {- can also get trajectories, selected_cvs, states, and model -}
            all_state_structures = "state_structures" af2rave_results
        in
            map
                (λ state_structures_i →
                    let
                        {- each state has one to many representative structures -}
                        state_structure = get 0 state_structures_i,
                        {- can also get structure_name and frame_index -}
                        trc = get (download ("trc" state_structure))
                    in
                        save Structure {
                            topology = upload (get 0 trc),
                            residues = upload (get 1 trc),
                            chains = upload (get 2 trc),
                            rcsb_id = none
                        }
                )
                all_state_structures
"""


@pytest.mark.asyncio
async def test_af2rave(
    provider: Provider,
):
    r = await provider.eval_rex(af2rave_rex)
    print(r)
    assert r is False
