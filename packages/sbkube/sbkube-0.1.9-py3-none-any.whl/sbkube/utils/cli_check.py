import shutil
import subprocess
import sys
import os
from rich.console import Console

console = Console()

def check_helm_installed_or_exit():
    helm_path = shutil.which("helm")
    if not helm_path:
        console.print("[red]❌ helm 명령이 시스템에 설치되어 있지 않습니다.[/red]")
        sys.exit(1)

    try:
        result = subprocess.run(["helm", "version"], capture_output=True, text=True, check=True)
        console.print(f"[green]✅ helm 확인됨:[/green] {result.stdout.strip()}")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]❌ helm 실행 실패:[/red] {e}")
        sys.exit(1)
    except PermissionError:
        console.print(f"[red]❌ helm 바이너리에 실행 권한이 없습니다: {helm_path}[/red]")
        sys.exit(1)

def check_kubectl_installed_or_exit(kubeconfig: str | None = None, kubecontext: str | None = None):
    kubectl_path = shutil.which("kubectl")
    if not kubectl_path:
        console.print("[red]❌ kubectl 명령이 시스템에 설치되어 있지 않습니다.[/red]")
        sys.exit(1)

    try:
        cmd = ["kubectl", "version", "--client"]
        if kubeconfig:
            cmd.extend(["--kubeconfig", kubeconfig])
        if kubecontext:
            cmd.extend(["--context", kubecontext])
        
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        console.print(f"[green]✅ kubectl 확인됨:[/green] {result.stdout.strip()}")
    except subprocess.CalledProcessError as e:
        console.print(f"[red]❌ kubectl 실행 실패:[/red] {e}")
        sys.exit(1)
    except PermissionError:
        console.print(f"[red]❌ kubectl 바이너리에 실행 권한이 없습니다: {kubectl_path}[/red]")
        sys.exit(1)

def print_helm_connection_help():
    import subprocess
    import os
    from pathlib import Path
    import json
    import shutil
    home = str(Path.home())
    helm_dir = os.path.join(home, ".config", "helm")
    # 0. helm 설치 여부
    if shutil.which("helm") is None:
        print("\n❌ helm 명령이 시스템에 설치되어 있지 않습니다.")
        print("Helm을 설치하거나, asdf 등 버전 매니저에서 helm 버전을 활성화하세요.")
        print("https://helm.sh/docs/intro/install/")
        return
    # 1. repo 목록
    try:
        result = subprocess.run([
            "helm", "repo", "list", "-o", "json"
        ], capture_output=True, text=True, check=True)
        repos = json.loads(result.stdout)
    except Exception as e:
        print("\n⚠️ helm이 정상적으로 동작하지 않습니다.")
        print(f"에러: {e}")
        print("helm version, helm repo list 명령이 정상 동작하는지 확인하세요.")
        return
    # 2. repo 파일 목록
    try:
        repo_files = []
        if os.path.isdir(helm_dir):
            repo_files = [f for f in os.listdir(helm_dir) if os.path.isfile(os.path.join(helm_dir, f))]
    except Exception:
        repo_files = []
    # 3. 안내 메시지
    if repos:
        print("등록된 helm repo 목록:")
        for repo in repos:
            print(f"  * {repo.get('name', '')}: {repo.get('url', '')}")
        print("helm repo add <name> <url> 명령으로 repo를 추가할 수 있습니다.")
    else:
        print("등록된 helm repo가 없습니다.")
    if repo_files:
        print("\n~/.config/helm 디렉토리 내 파일:")
        for f in repo_files:
            print(f"  - {f}")
    print("helm version, helm repo list 명령이 정상 동작하는지 확인하세요.\n")


def print_kube_contexts():
    try:
        result = subprocess.run(
            ["kubectl", "config", "get-contexts", "-o", "name"],
            capture_output=True, text=True, check=True
        )
        contexts = result.stdout.strip().splitlines()
        print("사용 가능한 context 목록:")
        for ctx in contexts:
            print(f"  * {ctx}")
        print("kubectl config use-context <context명> 명령으로 클러스터를 선택하세요.")
    except Exception as e:
        print("kubectl context 목록을 가져올 수 없습니다:", e)

def print_kube_connection_help():
    import glob
    import getpass
    from pathlib import Path
    import platform
    home = str(Path.home())
    kube_dir = os.path.join(home, ".kube")
    config_path = os.path.join(kube_dir, "config")
    # 1. context 목록
    try:
        result = subprocess.run([
            "kubectl", "config", "get-contexts", "-o", "name"
        ], capture_output=True, text=True, check=True)
        contexts = result.stdout.strip().splitlines()
    except Exception:
        contexts = []
    # 2. ~/.kube 디렉토리 내 파일 목록 (config 제외)
    try:
        files = [f for f in os.listdir(kube_dir) if os.path.isfile(os.path.join(kube_dir, f)) and f != "config"]
    except Exception:
        files = []
    # 3. 안내 메시지
    print("\n⚠️ kubectl이 현재 클러스터에 연결되어 있지 않습니다.")
    if contexts:
        print("사용 가능한 context 목록:")
        for ctx in contexts:
            print(f"  * {ctx}")
        print("kubectl config use-context <context명> 명령으로 클러스터를 선택하세요.")
    else:
        print("사용 가능한 context가 없습니다.")
    if files:
        print("\n~/.kube 디렉토리 내 추가 kubeconfig 파일:")
        for f in files:
            print(f"  - {f}")
        print("\nexport KUBECONFIG=~/.kube/<파일명> 명령으로 해당 클러스터에 연결할 수 있습니다.")
    print("")

def print_helm_connection_help():
    import subprocess
    import os
    from pathlib import Path
    import json
    home = str(Path.home())
    helm_dir = os.path.join(home, ".config", "helm")
    # 1. repo 목록
    try:
        result = subprocess.run([
            "helm", "repo", "list", "-o", "json"
        ], capture_output=True, text=True, check=True)
        repos = json.loads(result.stdout)
    except Exception:
        repos = []
    # 2. repo 파일 목록
    try:
        repo_files = []
        if os.path.isdir(helm_dir):
            repo_files = [f for f in os.listdir(helm_dir) if os.path.isfile(os.path.join(helm_dir, f))]
    except Exception:
        repo_files = []
    # 3. 안내 메시지
    print("\n⚠️ helm이 정상적으로 동작하지 않습니다.")
    if repos:
        print("등록된 helm repo 목록:")
        for repo in repos:
            print(f"  * {repo.get('name', '')}: {repo.get('url', '')}")
        print("helm repo add <name> <url> 명령으로 repo를 추가할 수 있습니다.")
    else:
        print("등록된 helm repo가 없습니다.")
    if repo_files:
        print("\n~/.config/helm 디렉토리 내 파일:")
        for f in repo_files:
            print(f"  - {f}")
    print("helm version, helm repo list 명령이 정상 동작하는지 확인하세요.\n")